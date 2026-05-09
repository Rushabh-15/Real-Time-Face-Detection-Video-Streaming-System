/// <reference types="vite/client" />

/**
 * Typed Vite environment variables.
 *
 * Values come from the monorepo-root `.env` (Vite is configured with
 * `envDir: ".."`). Declaring them here makes `import.meta.env.VITE_FOO`
 * a typed `string` rather than `any` — strict mode requires it.
 */
interface ImportMetaEnv {
  readonly VITE_BACKEND_WS_URL: string;
  readonly VITE_BACKEND_HTTP_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}