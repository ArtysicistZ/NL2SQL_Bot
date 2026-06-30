// The slim Plotly bundle ships no types; reuse the full @types/plotly.js.
declare module "plotly.js-dist-min" {
  import type Plotly from "plotly.js";
  export * from "plotly.js";
  const value: typeof Plotly;
  export default value;
}
