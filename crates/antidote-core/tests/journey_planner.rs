use antidote_core::contracts::{
    JourneyPlanControlPolicy, JourneyPlanControlPolicySupportedControl,
    JourneyPlanDerivationSource, MomentContext, MomentContextDesiredTransitionDirection,
};
use antidote_core::{
    JourneyEdit, PlanningError, RuleGuidedPlanner, hash_journey_plan, validate_inspectable_plan,
    validate_plan_for_moment,
};
use serde::de::DeserializeOwned;
use serde_json::Value;

fn fixture<T: DeserializeOwned>(name: &str) -> T {
    let suite: Value = serde_json::from_str(include_str!("../../../contracts/fixtures/cases.json"))
        .expect("canonical fixture suite must parse");
    let data = suite["cases"]
        .as_array()
        .expect("fixture cases must be an array")
        .iter()
        .find(|case| case["name"] == name)
        .expect("named fixture must exist")["data"]
        .clone();
    serde_json::from_value(data).expect("valid fixture must match generated type")
}

fn moment() -> MomentContext {
    fixture("moment-context-valid")
}

#[test]
fn fixed_input_produces_stable_schema_valid_plan() {
    let planner = RuleGuidedPlanner::default();
    let moment = moment();
    let first = planner
        .propose("journey-stable", &moment)
        .expect("synthetic input must plan");
    let second = planner
        .propose("journey-stable", &moment)
        .expect("same synthetic input must plan");

    assert_eq!(first, second);
    validate_plan_for_moment(&moment, &first).expect("plan must be executable in its moment");
    antidote_core::contracts::validate_contract(
        "journey-plan",
        &serde_json::to_value(first).expect("plan must serialize"),
    )
    .expect("planner output must satisfy the canonical schema");
}

#[test]
fn duration_reconciliation_holds_across_every_schema_boundary() {
    let planner = RuleGuidedPlanner::default();
    let mut moment = moment();
    for duration in (10..=3600).step_by(37).chain([3600]) {
        moment.time_horizon_seconds = duration;
        let plan = planner
            .propose("journey-duration-property", &moment)
            .expect("every contract-valid horizon must plan");
        assert_eq!(
            plan.stages
                .iter()
                .map(|stage| stage.duration_seconds)
                .sum::<i64>(),
            duration
        );
        assert!(plan.stages.iter().all(|stage| stage.duration_seconds >= 1));
    }
}

#[test]
fn every_transition_direction_produces_a_trace_complete_plan() {
    let planner = RuleGuidedPlanner::default();
    let mut moment = moment();
    let directions = [
        MomentContextDesiredTransitionDirection::StayWith,
        MomentContextDesiredTransitionDirection::Soften,
        MomentContextDesiredTransitionDirection::Regulate,
        MomentContextDesiredTransitionDirection::Uplift,
        MomentContextDesiredTransitionDirection::Focus,
        MomentContextDesiredTransitionDirection::Release,
        MomentContextDesiredTransitionDirection::Explore,
        MomentContextDesiredTransitionDirection::Other,
    ];
    for direction in directions {
        moment.desired_transition.direction = direction;
        let plan = planner
            .propose("journey-direction-property", &moment)
            .expect("every declared direction must plan");
        validate_inspectable_plan(&plan).expect("all proposed controls must have a trace");
    }
}

#[test]
fn person_edits_create_a_new_hashed_revision_and_replace_traces() {
    let planner = RuleGuidedPlanner::default();
    let moment = moment();
    let original = planner
        .propose("journey-original", &moment)
        .expect("initial proposal must plan");
    let mut controls = original.stages[1].acoustic_controls.clone();
    controls.tempo_bpm = Some(74.0);
    controls.density = Some(0.35);
    let revised = planner
        .revise(
            &original,
            "journey-revised",
            &moment,
            &[
                JourneyEdit::Strategy("use the person's edited sparse arc".to_owned()),
                JourneyEdit::StageSemanticIntent {
                    stage_index: 1,
                    semantic_intent: vec![
                        "leave more room around the central transition".to_owned(),
                    ],
                },
                JourneyEdit::StageAcousticControls {
                    stage_index: 1,
                    acoustic_controls: controls,
                },
            ],
        )
        .expect("bounded person edits must create a replacement");

    assert_eq!(revised.revision, Some(2));
    assert_eq!(
        revised.supersedes_plan_id.as_deref(),
        Some("journey-original")
    );
    assert_ne!(revised.plan_hash, original.plan_hash);
    assert_eq!(revised.strategy, "use the person's edited sparse arc");
    assert!(revised.derivations.as_ref().is_some_and(|derivations| {
        derivations.iter().any(|derivation| {
            derivation.target == "/stages/1/acoustic_controls/tempo_bpm"
                && derivation.source == JourneyPlanDerivationSource::PersonEdit
        })
    }));
    validate_plan_for_moment(&moment, &revised).expect("replacement must remain executable");
}

#[test]
fn contradictory_preferences_and_excluded_instructions_fail_closed() {
    let planner = RuleGuidedPlanner::default();
    let mut contradictory = moment();
    contradictory.inclusions = vec!["soft sustained texture".to_owned()];
    contradictory.exclusions = vec!["  Soft Sustained Texture  ".to_owned()];
    assert_eq!(
        planner.propose("journey-contradictory", &contradictory),
        Err(PlanningError::ContradictoryPreference)
    );

    let mut excluded = moment();
    excluded.exclusions = vec!["soft sustained texture".to_owned()];
    assert_eq!(
        planner.propose("journey-excluded", &excluded),
        Err(PlanningError::ExcludedInstruction)
    );
}

#[test]
fn unsafe_intensity_and_unsupported_controls_fail_closed() {
    let moment = moment();
    let planner = RuleGuidedPlanner::default();
    let original = planner
        .propose("journey-policy-original", &moment)
        .expect("default proposal must plan");
    let mut over_ceiling = original.stages[0].acoustic_controls.clone();
    over_ceiling.density = Some(0.95);
    assert_eq!(
        planner.revise(
            &original,
            "journey-over-ceiling",
            &moment,
            &[JourneyEdit::StageAcousticControls {
                stage_index: 0,
                acoustic_controls: over_ceiling,
            }],
        ),
        Err(PlanningError::ControlPolicyViolation)
    );

    let restricted = RuleGuidedPlanner::new(JourneyPlanControlPolicy {
        supported_controls: vec![JourneyPlanControlPolicySupportedControl::TempoBpm],
        stagewise_controls: true,
        tempo_bpm_min: 48.0,
        tempo_bpm_max: 112.0,
        density_ceiling: 0.0,
        spatiality_ceiling: 0.0,
    })
    .expect("restricted policy itself is valid");
    let restricted_plan = restricted
        .propose("journey-restricted", &moment)
        .expect("planner must omit unavailable controls");
    let mut unsupported = restricted_plan.stages[0].acoustic_controls.clone();
    unsupported.timbre = Some(vec!["synthetic unsupported timbre".to_owned()]);
    assert_eq!(
        restricted.revise(
            &restricted_plan,
            "journey-unsupported",
            &moment,
            &[JourneyEdit::StageAcousticControls {
                stage_index: 0,
                acoustic_controls: unsupported,
            }],
        ),
        Err(PlanningError::UnsupportedControl)
    );
}

#[test]
fn tampering_and_prohibited_rule_claims_fail_even_with_a_recomputed_hash() {
    let planner = RuleGuidedPlanner::default();
    let moment = moment();
    let mut tampered = planner
        .propose("journey-tamper", &moment)
        .expect("proposal must plan");
    tampered.strategy.push_str(" with unrecorded mutation");
    assert_eq!(
        validate_inspectable_plan(&tampered),
        Err(PlanningError::PlanHashMismatch)
    );

    let mut prohibited = planner
        .propose("journey-claim", &moment)
        .expect("proposal must plan");
    prohibited
        .derivations
        .as_mut()
        .expect("planner must emit derivations")[0]
        .rationale = "This will cure the person's state.".to_owned();
    prohibited.plan_hash = Some(hash_journey_plan(&prohibited).expect("plan must hash"));
    assert_eq!(
        validate_inspectable_plan(&prohibited),
        Err(PlanningError::ProhibitedRuleClaim)
    );
}
