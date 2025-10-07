<svelte:options
  customElement={{ tag: "websocket-preference", shadow: "none" }}
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
    "package-websocket",
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
          Websocket Preference <div
            style="margin-left: 12px; width: 12px; height: 12px; border-radius: 50%; background-color: {currentlyConnected
              ? '#00D248'
              : '#fb2323'}"
          />
        </div>
      </BlockTitle>
      <BlockBody>
        Connection to client : {currentlyConnected ? "Connected" : "Connecting"}
      </BlockBody>
      <BlockBody>
        Window focus
        <MeltCheckbox
          title={"Only run actions when Window is in focus"}
          bind:target={watchForActiveWindow}
        />
        <p class="text-gray-500 text-sm font-bold mt-1">
          Note: Requires Active Window package enabled
        </p>
      </BlockBody>
    </Block>
  </div>
</main-app>
