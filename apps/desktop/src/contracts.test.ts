import { describe, expect, it } from "vitest";

import fixtures from "../../../contracts/fixtures/cases.json";
import {
  contractValidationErrors,
  type ContractName,
  validateContract,
} from "./contracts";

interface FixtureCase {
  name: string;
  contract: ContractName;
  valid: boolean;
  data: unknown;
}

describe("canonical Antidote fixtures", () => {
  for (const fixture of fixtures.cases as FixtureCase[]) {
    it(`${fixture.name} has the declared validity`, () => {
      const valid = validateContract(fixture.contract, fixture.data);

      expect(valid, contractValidationErrors()).toBe(fixture.valid);
    });
  }
});
