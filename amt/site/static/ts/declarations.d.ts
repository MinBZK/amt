// Ambient module declarations for imports TypeScript cannot resolve on its own.
// TypeScript 6.0 tightened this: side-effect imports of non-code modules now need
// a declaration (TS2882), and untyped modules error under strict mode (TS7016).
//
// - "*.scss": stylesheets are bundled by webpack, not consumed as TS values.
// - "hyperscript.org": the runtime package has no bundled types; @types/hyperscript
//   only declares the "hyperscript" module, not the "hyperscript.org" entry point.
declare module "*.scss";
declare module "hyperscript.org";
