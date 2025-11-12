<svelte:options
  customElement={{ tag: "package-touchdesigner-parhover-preference", shadow: "none" }}
/>

<script>
  import {
    Block,
    BlockBody,
    BlockTitle,
    BlockRow,
    MoltenPushButton,
    MeltCheckbox,
    MeltSlider,
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
  let inactivityTimeoutMinutes = 0; // Default off
  let screenDimLevel = 0; // 0-100%, 0 = fully off
  let screenActiveLevel = 100; // 0-100%, 100 = full brightness
  let isReceivingUpdate = false;
  let hasReceivedInitialStatus = false; // Prevent sending defaults before receiving initial state

  $: {
    watchForActiveWindow;
    controlScreenOnConnection;
    controlLedOnConnection;
    inactivityTimeoutMinutes;
    screenDimLevel;
    screenActiveLevel;
    if (!isReceivingUpdate && hasReceivedInitialStatus) {
      messagePort.postMessage({
        type: "set-setting",
        watchForActiveWindow,
        controlScreenOnConnection,
        controlLedOnConnection,
        inactivityTimeoutMinutes,
        screenDimLevel,
        screenActiveLevel,
      });
    }
  }

  onMount(() => {
    messagePort.onmessage = (e) => {
      const data = e.data;
      if (data.type === "clientStatus") {
        isReceivingUpdate = true;
        currentlyConnected = data.clientConnected;
        watchForActiveWindow = data.watchForActiveWindow;
        // Use explicit undefined checks for booleans to ensure false values are preserved
        controlScreenOnConnection = data.controlScreenOnConnection !== undefined ? data.controlScreenOnConnection : false;
        controlLedOnConnection = data.controlLedOnConnection !== undefined ? data.controlLedOnConnection : true;
        inactivityTimeoutMinutes = data.inactivityTimeoutMinutes ?? 5;
        screenDimLevel = data.screenDimLevel ?? 0;
        screenActiveLevel = data.screenActiveLevel ?? 100;
        setTimeout(() => { 
          isReceivingUpdate = false;
          hasReceivedInitialStatus = true; // Enable reactive statement after initial state is loaded
        }, 10);
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
        <div class="flex flex-col gap-4">
          <MeltCheckbox
            title={"Set LEDs when TouchDesigner is disconnected"}
            bind:target={controlLedOnConnection}
          />
          <MeltCheckbox
            title={"Turn off screen when TouchDesigner is disconnected"}
            bind:target={controlScreenOnConnection}
          />
          
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">
              Screen inactivity timeout (minutes, 0 = disabled)
            </label>
            <input
              type="number"
              bind:value={inactivityTimeoutMinutes}
              min="0"
              max="60"
              step="0.1"
              class="px-3 py-2 bg-primary border border-secondary rounded-md text-sm"
            />
            <span class="text-xs text-secondary-content">
              {inactivityTimeoutMinutes === 0 
                ? 'Timeout disabled' 
                : `Screen dims after specified inactivity`}
            </span>
          </div>
          
          <BlockRow border="transparent">
            <div class="flex flex-col gap-1 flex-1">
              <label class="text-sm font-medium">
                Inactive brightness
              </label>
              <div class="flex items-center gap-2">
                <MeltSlider
                  bind:target={screenDimLevel}
                  min={0}
                  max={100}
                  step={1}
                />
                <span class="text-sm font-mono w-12 text-right">{screenDimLevel}%</span>
              </div>
              <span class="text-xs text-secondary-content">
                After timeout
              </span>
            </div>

            <div class="flex flex-col gap-1 flex-1">
              <label class="text-sm font-medium">
                Active brightness
              </label>
              <div class="flex items-center gap-2">
                <MeltSlider
                  bind:target={screenActiveLevel}
                  min={0}
                  max={100}
                  step={1}
                />
                <span class="text-sm font-mono w-12 text-right">{screenActiveLevel}%</span>
              </div>
              <span class="text-xs text-secondary-content">
                When active
              </span>
            </div>
            

          </BlockRow>
        </div>
      </BlockBody>
    </Block>
  </div>
</main-app>
