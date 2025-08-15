export const IPC_CHANNELS = {
  // Profile management
  PROFILE_GET: 'profile:get',
  PROFILE_SET: 'profile:set',

  // Authentication
  AUTH_LOGIN: 'auth:login',

  // Challenge handling
  CHALLENGE_CAPTCHA_DETECTED: 'challenge:captchaDetected',
  CHALLENGE_AWAIT_USER_ACTION: 'challenge:awaitUserAction',

  // Capture operations
  CAPTURE_SINGLEFILE: 'capture:singlefile',
  CAPTURE_PDF: 'capture:pdf',

  // Queue management
  QUEUE_ENQUEUE: 'queue:enqueue',
  QUEUE_STATUS: 'queue:status',
  QUEUE_PAUSE_ITEM: 'queue:pauseItem',
  QUEUE_RESUME_ITEM: 'queue:resumeItem',

  // Settings
  SETTINGS_GET: 'settings:get',
  SETTINGS_SET: 'settings:set',

  // Network configuration
  CERTS_SET_CA_BUNDLE: 'certs:setCABundle',
  NETWORK_SET_PROXY: 'network:setProxy',

  // Utilities
  SHELL_OPEN_EXTERNAL: 'shell:openExternal',
  DIALOG_SHOW_SAVE: 'dialog:showSaveDialog',
  DIALOG_SHOW_OPEN: 'dialog:showOpenDialog',
} as const;
