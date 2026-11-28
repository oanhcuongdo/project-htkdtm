import { expect, it } from "vitest";
import { mapLinks } from "../src/utils/mapLinks";
it("uses public destination coordinates without origin or credentials", () => {
  const links = mapLinks(21, 105)!;
  expect(new URL(links.embed).searchParams.get("marker")).toBe("21,105");
  expect(new URL(links.directions).searchParams.get("destination")).toBe(
    "21,105",
  );
  expect(new URL(links.directions).searchParams.has("origin")).toBe(false);
});
it.each([
  [NaN, 0],
  [0, Infinity],
  [91, 0],
  [0, -181],
])("rejects invalid coordinates %s %s", (lat, lng) => {
  expect(mapLinks(lat, lng)).toBeNull();
});
it("accepts zero coordinates", () => {
  expect(mapLinks(0, 0)).not.toBeNull();
});
