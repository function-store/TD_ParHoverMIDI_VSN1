<svelte:options
  customElement={{ tag: "websocket-parameter-set-action", shadow: "none" }}
/>

<script>
  import { MeltCombo, MeltCheckbox } from "@intechstudio/grid-uikit";
  import { onMount } from "svelte";

  let parameterId = "";
  let parameterValue = "";

  let currentCodeValue = "";
  let ref;
  let isInitialized = false;

  const actionRegex = /^gps\("package-websocket", "*(.*?)", (.*?)\)$/;
  function actualCode() {
    return `gps("package-websocket", "${parameterId}", ${parameterValue})`;
  }

  function handleConfigUpdate(config) {
    if (currentCodeValue != config.script) {
      currentCodeValue = config.script;
      const match = config.script.match(actionRegex);
      if (match) {
        parameterId = match[1] ?? "";
        parameterValue = match[2] ?? "";
        console.log({ parameterId, parameterValue });
        isInitialized = true;
      }
    }
  }

  onMount(() => {
    const event = new CustomEvent("updateConfigHandler", {
      bubbles: true,
      detail: { handler: handleConfigUpdate },
    });
    ref.dispatchEvent(event);
  });

  $: (parameterId,
    parameterValue,
    isInitialized &&
      (function updateCode() {
        var code = actualCode();
        if (currentCodeValue != code) {
          currentCodeValue = code;
          const event = new CustomEvent("updateCode", {
            bubbles: true,
            detail: { script: String(code) },
          });
          if (ref) {
            ref.dispatchEvent(event);
          }
        }
      })());
</script>

<single-parameter-set
  class="{$$props.class} flex flex-col w-full pb-2 px-2 pointer-events-auto"
  bind:this={ref}
>
  <div class="w-full flex flex-row">
    <div style="width: 50%;">
      <MeltCombo
        title={"Parameter ID"}
        bind:value={parameterId}
        suggestions={[{ info: "Volume", value: "volume" }]}
        searchable={true}
        size={"full"}
      />
    </div>
    <div style="width: 50%;">
      <MeltCombo
        title={"Parameter value"}
        bind:value={parameterValue}
        size={"full"}
      />
    </div>
  </div>
</single-parameter-set>
