use std::collections::BTreeSet;
use std::error::Error;
use std::fmt::{Display, Formatter};

use antidote_contracts::{
    JourneyPlan, JourneyPlanControlPolicy, JourneyPlanControlPolicySupportedControl,
    JourneyPlanDerivation, JourneyPlanDerivationSource, JourneyPlanRuleSet, JourneyPlanStage,
    JourneyPlanStageAcousticControls, JourneyPlanStageRole, JourneyPlanStatus, MomentContext,
    MomentContextDesiredTransitionDirection, validate_contract,
};
use serde::Serialize;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

/// Stable identity of the first deterministic planning policy.
pub const RULE_SET_ID: &str = "antidote.level-1.transparent-journey";
/// Semantic version of the inspectable Level-1 policy.
pub const RULE_SET_VERSION: &str = "1.0.0";

const PLAN_SCHEMA_VERSION: &str = "1.0.0";
const RULE_UNCERTAINTY: &str =
    "This is a transparent prototype default, not a prediction of felt response or benefit.";
const PERSON_EDIT_UNCERTAINTY: &str =
    "This records the person's present instruction; the resulting experience remains unknown.";
const PROHIBITED_RULE_CLAIMS: &[&str] = &[
    "activate the brain",
    "brainwave entrainment",
    "cure",
    "diagnose",
    "guaranteed benefit",
    "heal the",
    "treat",
    "therapeutic efficacy",
];

/// Why a deterministic proposal or person edit was rejected.
#[derive(Debug, Clone, PartialEq, Eq)]
#[non_exhaustive]
pub enum PlanningError {
    /// A required identifier or edit value is empty.
    EmptyValue,
    /// Moment inclusions and exclusions contradict one another.
    ContradictoryPreference,
    /// A proposed instruction conflicts with an explicit exclusion.
    ExcludedInstruction,
    /// Stage durations or their total are inconsistent.
    InvalidDuration,
    /// A populated control is unavailable under the recorded policy.
    UnsupportedControl,
    /// A control exceeds the recorded conservative prototype boundary.
    ControlPolicyViolation,
    /// A rule-derived field has no unique, inspectable explanation.
    MissingDerivation,
    /// Rule language makes a prohibited efficacy or deterministic-mechanism claim.
    ProhibitedRuleClaim,
    /// A plan cannot be serialized or fails its canonical contract.
    InvalidPlan,
    /// The supplied plan hash does not match its immutable content.
    PlanHashMismatch,
    /// A replacement does not name the exact current plan revision.
    RevisionMismatch,
    /// A revision request contains no changes.
    EmptyEditSet,
    /// An edit references a stage that does not exist.
    StageMissing,
}

impl Display for PlanningError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        let message = match self {
            Self::EmptyValue => "a required planning value is empty",
            Self::ContradictoryPreference => "moment inclusions and exclusions contradict",
            Self::ExcludedInstruction => "a proposed instruction conflicts with an exclusion",
            Self::InvalidDuration => "journey durations are inconsistent",
            Self::UnsupportedControl => "journey uses an unsupported acoustic control",
            Self::ControlPolicyViolation => "journey exceeds its recorded control policy",
            Self::MissingDerivation => "journey choice lacks an inspectable derivation",
            Self::ProhibitedRuleClaim => "planner rule makes a prohibited claim",
            Self::InvalidPlan => "journey plan is invalid",
            Self::PlanHashMismatch => "journey plan hash does not match its content",
            Self::RevisionMismatch => "journey revision lineage does not match",
            Self::EmptyEditSet => "journey revision contains no edits",
            Self::StageMissing => "journey edit references a missing stage",
        };
        formatter.write_str(message)
    }
}

impl Error for PlanningError {}

/// One typed person edit. Revisions never mutate the earlier plan in place.
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub enum JourneyEdit {
    /// Replace the high-level musical strategy.
    Strategy(String),
    /// Replace one stage's semantic role.
    StageRole {
        /// Zero-based stage index.
        stage_index: usize,
        /// Person-selected role.
        role: JourneyPlanStageRole,
    },
    /// Replace one stage's duration; the total is recalculated from all stages.
    StageDuration {
        /// Zero-based stage index.
        stage_index: usize,
        /// Person-selected duration.
        duration_seconds: i64,
    },
    /// Replace all semantic instructions for one stage.
    StageSemanticIntent {
        /// Zero-based stage index.
        stage_index: usize,
        /// Person-selected semantic instructions.
        semantic_intent: Vec<String>,
    },
    /// Replace all acoustic controls for one stage.
    StageAcousticControls {
        /// Zero-based stage index.
        stage_index: usize,
        /// Person-selected acoustic instructions.
        acoustic_controls: JourneyPlanStageAcousticControls,
    },
    /// Replace the visible prototype constraints.
    SafetyConstraints(Vec<String>),
}

/// Deterministic, versioned Level-1 journey planner.
#[derive(Debug, Clone, PartialEq)]
pub struct RuleGuidedPlanner {
    control_policy: JourneyPlanControlPolicy,
}

impl Default for RuleGuidedPlanner {
    fn default() -> Self {
        Self {
            control_policy: JourneyPlanControlPolicy {
                supported_controls: vec![
                    JourneyPlanControlPolicySupportedControl::TempoBpm,
                    JourneyPlanControlPolicySupportedControl::TimeSignature,
                    JourneyPlanControlPolicySupportedControl::Timbre,
                    JourneyPlanControlPolicySupportedControl::Harmony,
                    JourneyPlanControlPolicySupportedControl::Density,
                    JourneyPlanControlPolicySupportedControl::Spatiality,
                    JourneyPlanControlPolicySupportedControl::Dynamics,
                ],
                stagewise_controls: true,
                tempo_bpm_min: 48.0,
                tempo_bpm_max: 112.0,
                density_ceiling: 0.65,
                spatiality_ceiling: 0.75,
            },
        }
    }
}

impl RuleGuidedPlanner {
    /// Construct a planner with an explicit, inspectable generator-control policy.
    ///
    /// # Errors
    ///
    /// Returns a policy error when bounds are contradictory or outside the
    /// journey contract's acoustic ranges.
    pub fn new(control_policy: JourneyPlanControlPolicy) -> Result<Self, PlanningError> {
        validate_control_policy(&control_policy)?;
        Ok(Self { control_policy })
    }

    /// Return the exact control policy copied into every proposal.
    #[must_use]
    pub const fn control_policy(&self) -> &JourneyPlanControlPolicy {
        &self.control_policy
    }

    /// Propose a deterministic draft for one approved moment context.
    ///
    /// The proposal is an editable instruction set, not a prediction or clinical
    /// recommendation. Equal inputs and policy produce equal plans.
    ///
    /// # Errors
    ///
    /// Fails on empty identifiers, contradictory preferences, excluded output,
    /// an invalid control policy, or a plan that cannot be sealed and validated.
    pub fn propose(
        &self,
        plan_id: &str,
        moment: &MomentContext,
    ) -> Result<JourneyPlan, PlanningError> {
        require_non_empty(plan_id)?;
        validate_control_policy(&self.control_policy)?;
        validate_moment_preferences(moment)?;

        let roles = roles_for_direction(&moment.desired_transition.direction);
        let durations = split_duration(moment.time_horizon_seconds)?;
        let mut derivations = vec![
            rule_derivation(
                "/strategy",
                "strategy.direction.v1",
                "The person's selected transition direction chooses one visible planning template.",
            ),
            rule_derivation(
                "/total_duration_seconds",
                "duration.moment-horizon.v1",
                "The proposal copies the person-selected moment horizon without extending it.",
            ),
            rule_derivation(
                "/safety_constraints",
                "constraints.prototype-boundaries.v1",
                "The proposal states its editable control ceilings and preserves explicit exclusions.",
            ),
        ];
        let mut stages = Vec::with_capacity(roles.len());
        for (index, role) in roles.into_iter().enumerate() {
            let stage = self.build_stage(plan_id, moment, index, role, durations[index]);
            add_stage_derivations(&mut derivations, index, &stage);
            stages.push(stage);
        }

        let input_hash = hash_serializable(&(moment, &self.control_policy))?;
        let mut plan = JourneyPlan {
            schema_version: PLAN_SCHEMA_VERSION.to_owned(),
            id: plan_id.to_owned(),
            session_id: moment.session_id.clone(),
            moment_context_id: moment.id.clone(),
            working_projection_id: moment.working_projection_id.clone(),
            status: JourneyPlanStatus::Draft,
            strategy: strategy_for_direction(&moment.desired_transition.direction).to_owned(),
            total_duration_seconds: moment.time_horizon_seconds,
            revision: Some(1),
            supersedes_plan_id: None,
            rule_set: Some(JourneyPlanRuleSet {
                id: RULE_SET_ID.to_owned(),
                version: RULE_SET_VERSION.to_owned(),
                input_hash,
            }),
            control_policy: Some(self.control_policy.clone()),
            stages,
            safety_constraints: safety_constraints(moment, &self.control_policy),
            derivations: Some(derivations),
            approved_at: None,
            plan_hash: None,
        };
        reject_excluded_instructions(moment, &plan)?;
        seal_plan(&mut plan)?;
        validate_plan_for_moment(moment, &plan)?;
        Ok(plan)
    }

    /// Apply person-selected changes as a new immutable plan revision.
    ///
    /// # Errors
    ///
    /// Fails if the current plan is untrusted, the edit set is empty, a stage is
    /// missing, or the replacement violates duration, exclusion, control, trace,
    /// or hashing rules.
    pub fn revise(
        &self,
        current: &JourneyPlan,
        replacement_plan_id: &str,
        moment: &MomentContext,
        edits: &[JourneyEdit],
    ) -> Result<JourneyPlan, PlanningError> {
        require_non_empty(replacement_plan_id)?;
        if edits.is_empty() {
            return Err(PlanningError::EmptyEditSet);
        }
        validate_plan_for_moment(moment, current)?;
        if current.control_policy.as_ref() != Some(&self.control_policy) {
            return Err(PlanningError::RevisionMismatch);
        }

        let mut replacement = current.clone();
        replacement_plan_id.clone_into(&mut replacement.id);
        replacement.status = JourneyPlanStatus::Draft;
        replacement.approved_at = None;
        replacement.supersedes_plan_id = Some(current.id.clone());
        replacement.revision = Some(
            current
                .revision
                .ok_or(PlanningError::RevisionMismatch)?
                .checked_add(1)
                .ok_or(PlanningError::RevisionMismatch)?,
        );
        replacement.plan_hash = None;

        for edit in edits {
            apply_edit(&mut replacement, edit)?;
        }
        replacement.total_duration_seconds = replacement
            .stages
            .iter()
            .try_fold(0_i64, |total, stage| {
                total.checked_add(stage.duration_seconds)
            })
            .ok_or(PlanningError::InvalidDuration)?;
        mark_person_edits(&mut replacement, edits)?;
        reject_excluded_instructions(moment, &replacement)?;
        seal_plan(&mut replacement)?;
        validate_plan_for_moment(moment, &replacement)?;
        Ok(replacement)
    }

    fn build_stage(
        &self,
        plan_id: &str,
        moment: &MomentContext,
        index: usize,
        role: JourneyPlanStageRole,
        duration_seconds: i64,
    ) -> JourneyPlanStage {
        let controls = controls_for_stage(
            &moment.desired_transition.direction,
            index,
            &self.control_policy,
        );
        JourneyPlanStage {
            id: format!("{plan_id}:stage:{}", index + 1),
            order: i64::try_from(index).unwrap_or_default(),
            role: role.clone(),
            duration_seconds,
            semantic_intent: vec![semantic_intent(&role, moment)],
            acoustic_controls: controls,
            transition_rationale: Some(
                "The stage order is a reviewable narrative scaffold; it does not predict response."
                    .to_owned(),
            ),
        }
    }
}

/// Compute the lowercase SHA-256 digest of all plan content except `plan_hash`.
///
/// # Errors
///
/// Returns [`PlanningError::InvalidPlan`] if the plan cannot be serialized.
pub fn hash_journey_plan(plan: &JourneyPlan) -> Result<String, PlanningError> {
    let mut content = plan.clone();
    content.plan_hash = None;
    hash_serializable(&content)
}

/// Validate schema, lineage metadata, trace coverage, control policy, and hash.
///
/// # Errors
///
/// Returns the first fail-closed planning error.
pub fn validate_inspectable_plan(plan: &JourneyPlan) -> Result<(), PlanningError> {
    let value = serde_json::to_value(plan).map_err(|_| PlanningError::InvalidPlan)?;
    validate_contract("journey-plan", &value).map_err(|_| PlanningError::InvalidPlan)?;
    if plan.status != JourneyPlanStatus::Draft || plan.approved_at.is_some() {
        return Err(PlanningError::InvalidPlan);
    }
    require_non_empty(&plan.id)?;
    let revision = plan.revision.ok_or(PlanningError::InvalidPlan)?;
    if revision < 1
        || (revision == 1 && plan.supersedes_plan_id.is_some())
        || (revision > 1 && plan.supersedes_plan_id.is_none())
    {
        return Err(PlanningError::RevisionMismatch);
    }
    let rule_set = plan.rule_set.as_ref().ok_or(PlanningError::InvalidPlan)?;
    if rule_set.id != RULE_SET_ID || rule_set.version != RULE_SET_VERSION {
        return Err(PlanningError::InvalidPlan);
    }
    let policy = plan
        .control_policy
        .as_ref()
        .ok_or(PlanningError::InvalidPlan)?;
    validate_control_policy(policy)?;
    validate_durations(plan)?;
    validate_controls(plan, policy)?;
    validate_derivations(plan)?;
    let expected_hash = hash_journey_plan(plan)?;
    if plan.plan_hash.as_deref() != Some(expected_hash.as_str()) {
        return Err(PlanningError::PlanHashMismatch);
    }
    Ok(())
}

/// Validate a sealed plan against the exact moment and policy input that produced it.
///
/// # Errors
///
/// Returns a lineage, contradiction, exclusion, policy, trace, or hash error.
pub fn validate_plan_for_moment(
    moment: &MomentContext,
    plan: &JourneyPlan,
) -> Result<(), PlanningError> {
    validate_inspectable_plan(plan)?;
    if plan.session_id != moment.session_id
        || plan.moment_context_id != moment.id
        || plan.working_projection_id != moment.working_projection_id
        || plan.total_duration_seconds != moment.time_horizon_seconds
    {
        return Err(PlanningError::RevisionMismatch);
    }
    validate_moment_preferences(moment)?;
    reject_excluded_instructions(moment, plan)?;
    let policy = plan
        .control_policy
        .as_ref()
        .ok_or(PlanningError::InvalidPlan)?;
    let expected_input_hash = hash_serializable(&(moment, policy))?;
    if plan
        .rule_set
        .as_ref()
        .map(|rule_set| rule_set.input_hash.as_str())
        != Some(expected_input_hash.as_str())
    {
        return Err(PlanningError::RevisionMismatch);
    }
    Ok(())
}

fn seal_plan(plan: &mut JourneyPlan) -> Result<(), PlanningError> {
    plan.plan_hash = Some(hash_journey_plan(plan)?);
    Ok(())
}

fn validate_control_policy(policy: &JourneyPlanControlPolicy) -> Result<(), PlanningError> {
    if policy.supported_controls.is_empty()
        || policy.tempo_bpm_min < 20.0
        || policy.tempo_bpm_max > 300.0
        || policy.tempo_bpm_min > policy.tempo_bpm_max
        || !(0.0..=1.0).contains(&policy.density_ceiling)
        || !(0.0..=1.0).contains(&policy.spatiality_ceiling)
    {
        return Err(PlanningError::ControlPolicyViolation);
    }
    if policy
        .supported_controls
        .iter()
        .enumerate()
        .any(|(index, control)| policy.supported_controls[index + 1..].contains(control))
    {
        return Err(PlanningError::ControlPolicyViolation);
    }
    Ok(())
}

fn validate_moment_preferences(moment: &MomentContext) -> Result<(), PlanningError> {
    let inclusions = normalized_set(&moment.inclusions)?;
    let exclusions = normalized_set(&moment.exclusions)?;
    if inclusions.intersection(&exclusions).next().is_some() {
        return Err(PlanningError::ContradictoryPreference);
    }
    Ok(())
}

fn normalized_set(values: &[String]) -> Result<BTreeSet<String>, PlanningError> {
    values
        .iter()
        .map(|value| {
            let normalized = value.trim().to_lowercase();
            if normalized.is_empty() {
                Err(PlanningError::EmptyValue)
            } else {
                Ok(normalized)
            }
        })
        .collect()
}

fn reject_excluded_instructions(
    moment: &MomentContext,
    plan: &JourneyPlan,
) -> Result<(), PlanningError> {
    let exclusions = normalized_set(&moment.exclusions)?;
    for stage in &plan.stages {
        let controls = &stage.acoustic_controls;
        let values = controls
            .timbre
            .iter()
            .flatten()
            .chain(controls.harmony.iter().flatten())
            .chain(controls.dynamics.iter().flatten());
        for value in values {
            let proposed = value.trim().to_lowercase();
            if exclusions.iter().any(|excluded| {
                proposed.contains(excluded.as_str()) || excluded.contains(proposed.as_str())
            }) {
                return Err(PlanningError::ExcludedInstruction);
            }
        }
    }
    Ok(())
}

fn validate_durations(plan: &JourneyPlan) -> Result<(), PlanningError> {
    let mut duration = 0_i64;
    let mut identifiers = BTreeSet::new();
    for (index, stage) in plan.stages.iter().enumerate() {
        if stage.duration_seconds < 1
            || stage.order != i64::try_from(index).map_err(|_| PlanningError::InvalidDuration)?
            || !identifiers.insert(stage.id.as_str())
        {
            return Err(PlanningError::InvalidDuration);
        }
        duration = duration
            .checked_add(stage.duration_seconds)
            .ok_or(PlanningError::InvalidDuration)?;
    }
    if duration != plan.total_duration_seconds || !(10..=3600).contains(&duration) {
        return Err(PlanningError::InvalidDuration);
    }
    Ok(())
}

fn validate_controls(
    plan: &JourneyPlan,
    policy: &JourneyPlanControlPolicy,
) -> Result<(), PlanningError> {
    for stage in &plan.stages {
        let controls = &stage.acoustic_controls;
        require_supported(
            controls.tempo_bpm.is_some(),
            JourneyPlanControlPolicySupportedControl::TempoBpm,
            policy,
        )?;
        require_supported(
            controls.key.is_some(),
            JourneyPlanControlPolicySupportedControl::Key,
            policy,
        )?;
        require_supported(
            controls.time_signature.is_some(),
            JourneyPlanControlPolicySupportedControl::TimeSignature,
            policy,
        )?;
        require_supported(
            controls.timbre.is_some(),
            JourneyPlanControlPolicySupportedControl::Timbre,
            policy,
        )?;
        require_supported(
            controls.harmony.is_some(),
            JourneyPlanControlPolicySupportedControl::Harmony,
            policy,
        )?;
        require_supported(
            controls.density.is_some(),
            JourneyPlanControlPolicySupportedControl::Density,
            policy,
        )?;
        require_supported(
            controls.spatiality.is_some(),
            JourneyPlanControlPolicySupportedControl::Spatiality,
            policy,
        )?;
        require_supported(
            controls.dynamics.is_some(),
            JourneyPlanControlPolicySupportedControl::Dynamics,
            policy,
        )?;
        if controls.tempo_bpm.is_some_and(|tempo| {
            tempo < policy.tempo_bpm_min || tempo > policy.tempo_bpm_max
        }) || controls
            .density
            .is_some_and(|density| density > policy.density_ceiling)
            || controls
                .spatiality
                .is_some_and(|spatiality| spatiality > policy.spatiality_ceiling)
        {
            return Err(PlanningError::ControlPolicyViolation);
        }
    }
    if !policy.stagewise_controls {
        let first = plan
            .stages
            .first()
            .ok_or(PlanningError::InvalidPlan)?;
        if plan
            .stages
            .iter()
            .skip(1)
            .any(|stage| stage.acoustic_controls != first.acoustic_controls)
        {
            return Err(PlanningError::UnsupportedControl);
        }
    }
    Ok(())
}

fn require_supported(
    populated: bool,
    control: JourneyPlanControlPolicySupportedControl,
    policy: &JourneyPlanControlPolicy,
) -> Result<(), PlanningError> {
    if populated && !policy.supported_controls.contains(&control) {
        Err(PlanningError::UnsupportedControl)
    } else {
        Ok(())
    }
}

fn validate_derivations(plan: &JourneyPlan) -> Result<(), PlanningError> {
    let derivations = plan
        .derivations
        .as_ref()
        .ok_or(PlanningError::MissingDerivation)?;
    let mut targets = BTreeSet::new();
    for derivation in derivations {
        require_non_empty(&derivation.target)?;
        require_non_empty(&derivation.rule_id)?;
        require_non_empty(&derivation.rationale)?;
        require_non_empty(&derivation.uncertainty)?;
        if !targets.insert(derivation.target.as_str()) {
            return Err(PlanningError::MissingDerivation);
        }
        if derivation.source == JourneyPlanDerivationSource::Rule {
            let rationale = derivation.rationale.to_lowercase();
            if PROHIBITED_RULE_CLAIMS
                .iter()
                .any(|claim| rationale.contains(claim))
            {
                return Err(PlanningError::ProhibitedRuleClaim);
            }
        }
    }
    for target in expected_derivation_targets(plan) {
        if !targets.contains(target.as_str()) {
            return Err(PlanningError::MissingDerivation);
        }
    }
    Ok(())
}

fn expected_derivation_targets(plan: &JourneyPlan) -> Vec<String> {
    let mut targets = vec![
        "/strategy".to_owned(),
        "/total_duration_seconds".to_owned(),
        "/safety_constraints".to_owned(),
    ];
    for (index, stage) in plan.stages.iter().enumerate() {
        let base = format!("/stages/{index}");
        targets.push(format!("{base}/role"));
        targets.push(format!("{base}/duration_seconds"));
        targets.push(format!("{base}/semantic_intent"));
        if stage.transition_rationale.is_some() {
            targets.push(format!("{base}/transition_rationale"));
        }
        add_control_targets(&mut targets, &base, &stage.acoustic_controls);
    }
    targets
}

fn add_control_targets(
    targets: &mut Vec<String>,
    base: &str,
    controls: &JourneyPlanStageAcousticControls,
) {
    let fields = [
        ("tempo_bpm", controls.tempo_bpm.is_some()),
        ("key", controls.key.is_some()),
        ("time_signature", controls.time_signature.is_some()),
        ("timbre", controls.timbre.is_some()),
        ("harmony", controls.harmony.is_some()),
        ("density", controls.density.is_some()),
        ("spatiality", controls.spatiality.is_some()),
        ("dynamics", controls.dynamics.is_some()),
    ];
    targets.extend(fields.into_iter().filter_map(|(field, populated)| {
        populated.then(|| format!("{base}/acoustic_controls/{field}"))
    }));
}

fn split_duration(total: i64) -> Result<[i64; 3], PlanningError> {
    if !(10..=3600).contains(&total) {
        return Err(PlanningError::InvalidDuration);
    }
    let first = (total * 3 / 10).max(1);
    let second = (total * 5 / 10).max(1);
    let third = total
        .checked_sub(first)
        .and_then(|remaining| remaining.checked_sub(second))
        .ok_or(PlanningError::InvalidDuration)?;
    if third < 1 {
        return Err(PlanningError::InvalidDuration);
    }
    Ok([first, second, third])
}

fn roles_for_direction(
    direction: &MomentContextDesiredTransitionDirection,
) -> [JourneyPlanStageRole; 3] {
    use JourneyPlanStageRole::{Close, Hold, Integrate, Meet, Release, Transition};
    match direction {
        MomentContextDesiredTransitionDirection::StayWith => [Meet, Hold, Close],
        MomentContextDesiredTransitionDirection::Release => [Meet, Release, Integrate],
        MomentContextDesiredTransitionDirection::Soften
        | MomentContextDesiredTransitionDirection::Regulate => [Meet, Transition, Integrate],
        MomentContextDesiredTransitionDirection::Uplift
        | MomentContextDesiredTransitionDirection::Focus
        | MomentContextDesiredTransitionDirection::Explore
        | MomentContextDesiredTransitionDirection::Other => [Meet, Transition, Close],
    }
}

fn strategy_for_direction(direction: &MomentContextDesiredTransitionDirection) -> &'static str {
    match direction {
        MomentContextDesiredTransitionDirection::StayWith => {
            "maintain continuity, then close with minimal change"
        }
        MomentContextDesiredTransitionDirection::Soften => {
            "begin sparsely, introduce gentle contrast, then reduce variation"
        }
        MomentContextDesiredTransitionDirection::Regulate => {
            "establish a predictable pulse, vary gradually, then return to continuity"
        }
        MomentContextDesiredTransitionDirection::Uplift => {
            "begin with continuity, add brighter motion, then close predictably"
        }
        MomentContextDesiredTransitionDirection::Focus => {
            "establish a clear pulse, narrow competing texture, then close steadily"
        }
        MomentContextDesiredTransitionDirection::Release => {
            "meet the stated moment, allow controlled expansion, then leave integration space"
        }
        MomentContextDesiredTransitionDirection::Explore => {
            "begin from a stable anchor, introduce bounded contrast, then close clearly"
        }
        MomentContextDesiredTransitionDirection::Other => {
            "begin from the person's description, introduce bounded contrast, then close clearly"
        }
    }
}

fn semantic_intent(role: &JourneyPlanStageRole, moment: &MomentContext) -> String {
    match role {
        JourneyPlanStageRole::Meet => {
            "reflect the stated current moment without assuming it should change".to_owned()
        }
        JourneyPlanStageRole::Hold => {
            "maintain continuity around the person's stated direction".to_owned()
        }
        JourneyPlanStageRole::Transition => format!(
            "introduce bounded contrast toward the person's stated direction: {}",
            moment.desired_transition.description
        ),
        JourneyPlanStageRole::Release => {
            "make room for the person's stated release direction without promising an outcome"
                .to_owned()
        }
        JourneyPlanStageRole::Integrate => {
            "reduce variation and leave space for the person to assess the experience".to_owned()
        }
        JourneyPlanStageRole::Close => "close with a predictable low-change ending".to_owned(),
        JourneyPlanStageRole::Other => {
            "follow the person's explicit stage instruction without inferring an outcome".to_owned()
        }
    }
}

fn controls_for_stage(
    direction: &MomentContextDesiredTransitionDirection,
    index: usize,
    policy: &JourneyPlanControlPolicy,
) -> JourneyPlanStageAcousticControls {
    let base_tempo: f64 = match direction {
        MomentContextDesiredTransitionDirection::StayWith => 64.0,
        MomentContextDesiredTransitionDirection::Soften => 60.0,
        MomentContextDesiredTransitionDirection::Regulate => 68.0,
        MomentContextDesiredTransitionDirection::Uplift => 84.0,
        MomentContextDesiredTransitionDirection::Focus => 76.0,
        MomentContextDesiredTransitionDirection::Release => 72.0,
        MomentContextDesiredTransitionDirection::Explore => 70.0,
        MomentContextDesiredTransitionDirection::Other => 68.0,
    };
    let effective_index = if policy.stagewise_controls { index } else { 0 };
    let tempo_offsets: [f64; 3] = [-4.0, 4.0, -2.0];
    let density: f64 = [0.20, 0.40, 0.25][effective_index];
    let spatiality: f64 = [0.30, 0.50, 0.35][effective_index];
    let supports = |control| policy.supported_controls.contains(&control);
    JourneyPlanStageAcousticControls {
        tempo_bpm: supports(JourneyPlanControlPolicySupportedControl::TempoBpm)
            .then(|| (base_tempo + tempo_offsets[effective_index]).clamp(
                policy.tempo_bpm_min,
                policy.tempo_bpm_max,
            )),
        key: None,
        time_signature: supports(JourneyPlanControlPolicySupportedControl::TimeSignature)
            .then(|| "4/4".to_owned()),
        timbre: supports(JourneyPlanControlPolicySupportedControl::Timbre)
            .then(|| vec!["soft sustained texture".to_owned()]),
        harmony: supports(JourneyPlanControlPolicySupportedControl::Harmony)
            .then(|| vec!["open low-tension voicing".to_owned()]),
        density: supports(JourneyPlanControlPolicySupportedControl::Density)
            .then(|| density.min(policy.density_ceiling)),
        spatiality: supports(JourneyPlanControlPolicySupportedControl::Spatiality)
            .then(|| spatiality.min(policy.spatiality_ceiling)),
        dynamics: supports(JourneyPlanControlPolicySupportedControl::Dynamics)
            .then(|| vec!["gradual level changes only".to_owned()]),
    }
}

fn safety_constraints(
    moment: &MomentContext,
    policy: &JourneyPlanControlPolicy,
) -> Vec<String> {
    let mut constraints = vec![
        "keep transitions gradual and person-reviewable".to_owned(),
        format!(
            "keep density at or below the prototype ceiling {:.2}",
            policy.density_ceiling
        ),
        format!(
            "keep spatiality at or below the prototype ceiling {:.2}",
            policy.spatiality_ceiling
        ),
    ];
    constraints.extend(
        moment
            .exclusions
            .iter()
            .map(|exclusion| format!("exclude: {}", exclusion.trim())),
    );
    constraints
}

fn rule_derivation(target: &str, rule_id: &str, rationale: &str) -> JourneyPlanDerivation {
    JourneyPlanDerivation {
        target: target.to_owned(),
        source: JourneyPlanDerivationSource::Rule,
        rule_id: rule_id.to_owned(),
        rationale: rationale.to_owned(),
        uncertainty: RULE_UNCERTAINTY.to_owned(),
    }
}

fn add_stage_derivations(
    derivations: &mut Vec<JourneyPlanDerivation>,
    index: usize,
    stage: &JourneyPlanStage,
) {
    let base = format!("/stages/{index}");
    derivations.extend([
        rule_derivation(
            &format!("{base}/role"),
            "stage.role-by-direction.v1",
            "The selected transition direction chooses an editable narrative role.",
        ),
        rule_derivation(
            &format!("{base}/duration_seconds"),
            "stage.duration-ratio.v1",
            "The moment horizon is split into fixed visible ratios that sum exactly to the total.",
        ),
        rule_derivation(
            &format!("{base}/semantic_intent"),
            "stage.semantic-scaffold.v1",
            "The stage role supplies a plain-language instruction for person review.",
        ),
        rule_derivation(
            &format!("{base}/transition_rationale"),
            "stage.sequence-explanation.v1",
            "The planner labels the sequence as a scaffold rather than an expected response.",
        ),
    ]);
    let controls = &stage.acoustic_controls;
    let control_rules = [
        (
            "tempo_bpm",
            controls.tempo_bpm.is_some(),
            "control.tempo-bounded.v1",
        ),
        (
            "key",
            controls.key.is_some(),
            "control.key-explicit.v1",
        ),
        (
            "time_signature",
            controls.time_signature.is_some(),
            "control.meter-default.v1",
        ),
        (
            "timbre",
            controls.timbre.is_some(),
            "control.timbre-default.v1",
        ),
        (
            "harmony",
            controls.harmony.is_some(),
            "control.harmony-default.v1",
        ),
        (
            "density",
            controls.density.is_some(),
            "control.density-bounded.v1",
        ),
        (
            "spatiality",
            controls.spatiality.is_some(),
            "control.spatiality-bounded.v1",
        ),
        (
            "dynamics",
            controls.dynamics.is_some(),
            "control.dynamics-gradual.v1",
        ),
    ];
    derivations.extend(control_rules.into_iter().filter_map(|(field, present, rule)| {
        present.then(|| {
            rule_derivation(
                &format!("{base}/acoustic_controls/{field}"),
                rule,
                "A bounded generator instruction is included so the person can inspect and replace it.",
            )
        })
    }));
}

fn apply_edit(plan: &mut JourneyPlan, edit: &JourneyEdit) -> Result<(), PlanningError> {
    match edit {
        JourneyEdit::Strategy(strategy) => {
            require_non_empty(strategy)?;
            plan.strategy.clone_from(strategy);
        }
        JourneyEdit::StageRole { stage_index, role } => {
            stage_mut(plan, *stage_index)?.role = role.clone();
        }
        JourneyEdit::StageDuration {
            stage_index,
            duration_seconds,
        } => {
            if *duration_seconds < 1 {
                return Err(PlanningError::InvalidDuration);
            }
            stage_mut(plan, *stage_index)?.duration_seconds = *duration_seconds;
        }
        JourneyEdit::StageSemanticIntent {
            stage_index,
            semantic_intent,
        } => {
            if semantic_intent.is_empty() {
                return Err(PlanningError::EmptyValue);
            }
            for value in semantic_intent {
                require_non_empty(value)?;
            }
            stage_mut(plan, *stage_index)?
                .semantic_intent
                .clone_from(semantic_intent);
        }
        JourneyEdit::StageAcousticControls {
            stage_index,
            acoustic_controls,
        } => {
            stage_mut(plan, *stage_index)?.acoustic_controls = acoustic_controls.clone();
        }
        JourneyEdit::SafetyConstraints(constraints) => {
            if constraints.is_empty() {
                return Err(PlanningError::EmptyValue);
            }
            for value in constraints {
                require_non_empty(value)?;
            }
            plan.safety_constraints.clone_from(constraints);
        }
    }
    Ok(())
}

fn mark_person_edits(
    plan: &mut JourneyPlan,
    edits: &[JourneyEdit],
) -> Result<(), PlanningError> {
    let edit_targets = edits
        .iter()
        .map(|edit| edit_targets(plan, edit))
        .collect::<Result<Vec<_>, _>>()?;
    let derivations = plan
        .derivations
        .as_mut()
        .ok_or(PlanningError::MissingDerivation)?;
    for (edit, targets) in edits.iter().zip(edit_targets) {
        if let JourneyEdit::StageAcousticControls { stage_index, .. } = edit {
            let prefix = format!("/stages/{stage_index}/acoustic_controls/");
            derivations.retain(|derivation| !derivation.target.starts_with(&prefix));
        }
        for target in targets {
            derivations.retain(|derivation| derivation.target != target);
            derivations.push(person_edit_derivation(&target));
        }
    }
    derivations.sort_by(|left, right| left.target.cmp(&right.target));
    Ok(())
}

fn edit_targets(plan: &JourneyPlan, edit: &JourneyEdit) -> Result<Vec<String>, PlanningError> {
    let targets = match edit {
        JourneyEdit::Strategy(_) => vec!["/strategy".to_owned()],
        JourneyEdit::StageRole { stage_index, .. } => {
            vec![format!("/stages/{stage_index}/role")]
        }
        JourneyEdit::StageDuration { stage_index, .. } => vec![
            format!("/stages/{stage_index}/duration_seconds"),
            "/total_duration_seconds".to_owned(),
        ],
        JourneyEdit::StageSemanticIntent { stage_index, .. } => {
            vec![format!("/stages/{stage_index}/semantic_intent")]
        }
        JourneyEdit::StageAcousticControls { stage_index, .. } => {
            let stage = plan
                .stages
                .get(*stage_index)
                .ok_or(PlanningError::StageMissing)?;
            let base = format!("/stages/{stage_index}");
            let mut targets = Vec::new();
            add_control_targets(&mut targets, &base, &stage.acoustic_controls);
            targets
        }
        JourneyEdit::SafetyConstraints(_) => vec!["/safety_constraints".to_owned()],
    };
    Ok(targets)
}

fn person_edit_derivation(target: &str) -> JourneyPlanDerivation {
    JourneyPlanDerivation {
        target: target.to_owned(),
        source: JourneyPlanDerivationSource::PersonEdit,
        rule_id: "person.edit.v1".to_owned(),
        rationale: "The person replaced this proposed choice before approval.".to_owned(),
        uncertainty: PERSON_EDIT_UNCERTAINTY.to_owned(),
    }
}

fn stage_mut(
    plan: &mut JourneyPlan,
    stage_index: usize,
) -> Result<&mut JourneyPlanStage, PlanningError> {
    plan.stages
        .get_mut(stage_index)
        .ok_or(PlanningError::StageMissing)
}

fn require_non_empty(value: &str) -> Result<(), PlanningError> {
    if value.trim().is_empty() {
        Err(PlanningError::EmptyValue)
    } else {
        Ok(())
    }
}

fn hash_serializable<T: Serialize>(value: &T) -> Result<String, PlanningError> {
    let value = serde_json::to_value(value).map_err(|_| PlanningError::InvalidPlan)?;
    let canonical = canonicalize(value);
    let bytes = serde_json::to_vec(&canonical).map_err(|_| PlanningError::InvalidPlan)?;
    Ok(format!("{:x}", Sha256::digest(bytes)))
}

fn canonicalize(value: Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut entries = object.into_iter().collect::<Vec<_>>();
            entries.sort_by(|left, right| left.0.cmp(&right.0));
            Value::Object(
                entries
                    .into_iter()
                    .map(|(key, value)| (key, canonicalize(value)))
                    .collect::<Map<_, _>>(),
            )
        }
        Value::Array(values) => Value::Array(values.into_iter().map(canonicalize).collect()),
        other => other,
    }
}
