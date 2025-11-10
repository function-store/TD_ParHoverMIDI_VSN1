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
  let controlScreenOnConnection = false;
  let controlLedOnConnection = true;
  let isReceivingUpdate = false;

  $: (watchForActiveWindow,
    controlScreenOnConnection,
    controlLedOnConnection,
    !isReceivingUpdate &&
      (function sendSettings() {
        messagePort.postMessage({
          type: "set-setting",
          watchForActiveWindow,
          controlScreenOnConnection,
          controlLedOnConnection,
        });
      })());

  onMount(() => {
    messagePort.onmessage = (e) => {
      const data = e.data;
      if (data.type === "clientStatus") {
        isReceivingUpdate = true;
        currentlyConnected = data.clientConnected;
        watchForActiveWindow = data.watchForActiveWindow;
        controlScreenOnConnection = data.controlScreenOnConnection ?? false;
        controlLedOnConnection = data.controlLedOnConnection ?? true;
        setTimeout(() => { isReceivingUpdate = false; }, 10);
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
            click={() => window.open('https://function-store.github.io/TD_ParHoverMIDI_VSN1/', '_blank')} 
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

    <Block>
      <BlockTitle>Settings</BlockTitle>
      <BlockBody>
        <div class="flex flex-col gap-2">
          <MeltCheckbox
            title={"Set LEDs when TouchDesigner is disconnected"}
            bind:target={controlLedOnConnection}
          />
          <MeltCheckbox
            title={"Turn off LCD when TouchDesigner is disconnected"}
            bind:target={controlScreenOnConnection}
          />
        </div>
      </BlockBody>
    </Block>
  </div>
</main-app>
