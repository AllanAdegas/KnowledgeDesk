interface IconProps {
  className?: string
}

/** Small hand-rolled icon set — kept dependency-free rather than pulling in an icon library. */

export function ChatIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className={className}>
      <path
        d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8A2.5 2.5 0 0 1 17.5 16H10l-4.5 4v-4H6.5A2.5 2.5 0 0 1 4 13.5v-8Z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function DocsIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className={className}>
      <path
        d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9.5A1.5 1.5 0 0 1 5.5 19V5A1.5 1.5 0 0 1 7 3.5Z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M14 3.5V8h4.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12.5h6M9 15.5h6" strokeLinecap="round" />
    </svg>
  )
}

export function AgentIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className={className}>
      <rect x="4.5" y="8" width="15" height="10.5" rx="3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 8V5M9 5.5h6" strokeLinecap="round" />
      <circle cx="9" cy="13" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="15" cy="13" r="1.1" fill="currentColor" stroke="none" />
      <path d="M9.5 16.5h5" strokeLinecap="round" />
    </svg>
  )
}

export function SendIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} className={className}>
      <path d="M4.5 12 19 5l-5.5 15-2.6-6.4L4.5 12Z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function UploadCloudIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className={className}>
      <path
        d="M7.5 17.5A4 4 0 0 1 6.8 9.6a5 5 0 0 1 9.8-1.4A3.75 3.75 0 0 1 16.5 15"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M12 20v-7M9.2 15.8 12 13l2.8 2.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function CheckCircleIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className={className}>
      <circle cx="12" cy="12" r="8.25" />
      <path d="m8.5 12.3 2.4 2.4 4.6-5.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function AlertCircleIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className={className}>
      <circle cx="12" cy="12" r="8.25" />
      <path d="M12 8v4.5" strokeLinecap="round" />
      <circle cx="12" cy="15.5" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function FileIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className={className}>
      <path
        d="M7 3.5h6.5l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 5.5 19V5A1.5 1.5 0 0 1 7 3.5Z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M13 3.5V8h4.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function SparkleIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M12 2.5c.5 3.4 2.1 5 5.5 5.5-3.4.5-5 2.1-5.5 5.5-.5-3.4-2.1-5-5.5-5.5 3.4-.5 5-2.1 5.5-5.5Z" />
      <path d="M19 15c.28 1.7 1.05 2.47 2.75 2.75-1.7.28-2.47 1.05-2.75 2.75-.28-1.7-1.05-2.47-2.75-2.75 1.7-.28 2.47-1.05 2.75-2.75Z" />
    </svg>
  )
}
