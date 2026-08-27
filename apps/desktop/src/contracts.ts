import Ajv2020, {
  type ErrorObject,
  type ValidateFunction,
} from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

import consentGrant from "../../../contracts/schemas/consent-grant.v1.schema.json";
import generationResult from "../../../contracts/schemas/generation-result.v1.schema.json";
import generationSpec from "../../../contracts/schemas/generation-spec.v1.schema.json";
import journeyPlan from "../../../contracts/schemas/journey-plan.v1.schema.json";
import momentContext from "../../../contracts/schemas/moment-context.v1.schema.json";
import responseObservation from "../../../contracts/schemas/response-observation.v1.schema.json";
import workingContextProjection from "../../../contracts/schemas/working-context-projection.v1.schema.json";
import type { ContractByName } from "./generated/contracts";

export type ContractName = keyof ContractByName;

const schemas: Record<ContractName, object> = {
  "consent-grant": consentGrant,
  "generation-result": generationResult,
  "generation-spec": generationSpec,
  "journey-plan": journeyPlan,
  "moment-context": momentContext,
  "response-observation": responseObservation,
  "working-context-projection": workingContextProjection,
};

const ajv = new Ajv2020({
  allErrors: true,
  strict: true,
  validateFormats: true,
});
addFormats(ajv);

const validators = new Map<ContractName, ValidateFunction<unknown>>(
  Object.entries(schemas).map(([name, schema]) => [
    name as ContractName,
    ajv.compile(schema),
  ]),
);

let latestErrors: ErrorObject[] | null | undefined;

export function validateContract<Name extends ContractName>(
  name: Name,
  value: unknown,
): value is ContractByName[Name] {
  const validator = validators.get(name);
  if (validator === undefined) {
    throw new Error(`Unknown Antidote contract: ${name}`);
  }
  const valid = validator(value);
  latestErrors = validator.errors;
  return valid;
}

export function contractValidationErrors(): string {
  return ajv.errorsText(latestErrors, { separator: "\n" });
}
