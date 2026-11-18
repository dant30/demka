export const LANDING_PATH = {
  BOSS: '/',
  ADMIN: '/',
  SALES_HELPER: '/pos',
  FIELD_AGENT: '/field',
};

export function landingPathFor(role) {
  return LANDING_PATH[role] || '/pos';
}

export function isBossRole(role) {
  return role === 'BOSS' || role === 'ADMIN';
}
