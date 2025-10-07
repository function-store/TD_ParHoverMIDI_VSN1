<svelte:options
  customElement={{ tag: "package-touchdesigner-parhover-preference", shadow: "none" }}
/>

<script>
  import {
    Block,
    BlockBody,
    BlockTitle,
    MoltenPushButton,
    MeltCheckbox,
  } from "@intechstudio/grid-uikit";
  import { onMount } from "svelte";

  let currentlyConnected = false;

  // @ts-ignore
  const messagePort = createPackageMessagePort(
    "package-touchdesigner-parhover",
    "preferences",
  );

  let watchForActiveWindow = false;

  $: (watchForActiveWindow, handleDataChange());

  function handleDataChange() {
    messagePort.postMessage({
      type: "set-setting",
      watchForActiveWindow,
    });
  }

  onMount(() => {
    messagePort.onmessage = (e) => {
      const data = e.data;
      if (data.type === "clientStatus") {
        currentlyConnected = data.clientConnected;
        watchForActiveWindow = data.watchForActiveWindow;
      }
    };
    messagePort.start();
    return () => {
      messagePort.close();
    };
  });
</script>

<main-app>
  <div class="px-4 bg-secondary rounded-lg">
    <Block>
      <BlockTitle>
        <div class="flex flex-row content-center">
          TouchDesigner Par Hover (VSN1) <div
            style="margin-left: 12px; width: 12px; height: 12px; border-radius: 50%; background-color: {currentlyConnected
              ? '#00D248'
              : '#fb2323'}"
          />
        </div>
      </BlockTitle>
      <BlockBody>
        Connection to client : {currentlyConnected ? "Connected" : "Connecting"}
      </BlockBody>
    </Block>
    
    <Block>
      <BlockTitle>TouchDesigner Instructions and .tox</BlockTitle>
      <BlockBody>
        Check the README for instructions!
      </BlockBody>
        <div class="flex flex-row gap-2">
          <MoltenPushButton 
            text="README" 
            style="normal" 
            click={() => window.open('https://github.com/function-store/TD_ParHoverMIDI_VSN1?tab=readme-ov-file#quick-start', '_blank')} 
          />
          <MoltenPushButton 
            text="Download .tox" 
            style="accept" 
            click={() => window.open('https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest/download/ParHoverMIDI_VSN1.tox', '_blank')} 
          />
          <MoltenPushButton 
            text="Video Demo (placeholder)" 
            style="outlined" 
            click={() => window.open('https://youtube.com/c/FunctionStore', '_blank')} 
          />
        </div>
    </Block>
  </div>
</main-app>
