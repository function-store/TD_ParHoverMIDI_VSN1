import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { sveltePreprocess } from "svelte-preprocess";
import { notifyEditorAfterBuildPlugin } from "./vite.postbuild";

export default defineConfig({
  plugins: [
    svelte({
      preprocess: sveltePreprocess(),
      include: /\.svelte$/,
      compilerOptions: {
        customElement: true,
      },
      emitCss: false,
    }),
    notifyEditorAfterBuildPlugin(),
  ],
  build: {
    sourcemap: true,
    target: "modules",
    lib: {
      entry: "src/main.js",
      name: "<<name>>",
      fileName: "components",
    },
  },
});
