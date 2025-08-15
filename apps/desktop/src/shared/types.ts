export type ExecutionProfile = 'standard' | 'safe' | 'guided';

export type URLItemStatus = 
  | 'queued' 
  | 'running' 
  | 'waiting_captcha' 
  | 'waiting_user' 
  | 'done' 
  | 'failed' 
  | 'skipped';

export interface URLItem {
  url: string;
  depth: number;
  status: URLItemStatus;
  formats: {
    json?: boolean;
    md?: boolean;
    html?: boolean;
    pdf?: boolean;
  };
  attempts: number;
  error?: string;
  outputs?: {
    jsonPath?: string;
    mdPath?: string;
    singlefileHtmlPath?: string;
    pdfPath?: string;
  };
  profile: ExecutionProfile;
  startedAt?: string;
  finishedAt?: string;
}

export interface CrawlSettings {
  startUrl: string;
  depth: number;
  maxPages: number;
  allowedDomains: string[];
  disallowedPaths: string[];
  concurrency: number;
  delay: number;
  respectRobots: boolean;
  outputDirectory: string;
  formats: {
    json: boolean;
    markdown: boolean;
    html: boolean;
    pdf: boolean;
  };
  crawlPdfLinks: boolean;
  profile: ExecutionProfile;
  proxy?: {
    http?: string;
    https?: string;
  };
  caBundlePath?: string;
}

export interface QueueStats {
  running: number;
  waiting: number;
  done: number;
  failed: number;
  total: number;
}

export interface ChallengeInfo {
  url: string;
  type: 'captcha' | 'auth' | 'manual';
  provider?: string;
  screenshotPath?: string;
}

export interface UserAction {
  action: 'continue' | 'retry' | 'skip' | 'abort';
  overrides?: {
    delayMs?: number;
    concurrency?: number;
  };
}

export interface ProfileConfig {
  concurrency: number;
  delay: number;
  jitter: number;
  respectRobots: boolean;
  timeout: number;
  retries: number;
  backoffMultiplier: number;
}

export interface RunReport {
  id: string;
  startTime: string;
  endTime?: string;
  profile: ExecutionProfile;
  settings: CrawlSettings;
  items: URLItem[];
  stats: QueueStats;
  kpis: {
    pagesPerHour: number;
    successRate: number;
  };
}
