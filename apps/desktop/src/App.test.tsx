import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("Antidote desktop scaffold", () => {
  it("describes the foundation without claiming an implemented session", () => {
    const markup = renderToStaticMarkup(<App />);

    expect(markup).toContain("Foundation status");
    expect(markup).toContain("session experience itself is not implemented");
    expect(markup).toContain("No real audio model is installed");
  });
});
