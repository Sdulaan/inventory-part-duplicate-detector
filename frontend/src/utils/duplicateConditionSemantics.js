export const SITE_CONDITION_HELP = 'Must match when selected'
export const DEFAULT_CONDITION_HELP = 'Used for candidate discovery and scoring'

export function duplicateConditionHelp(field) {
  return field === 'CONTRACT' ? SITE_CONDITION_HELP : DEFAULT_CONDITION_HELP
}
