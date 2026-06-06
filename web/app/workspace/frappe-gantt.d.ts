// W11.C: minimal ambient typing for frappe-gantt — the package ships no
// .d.ts and we use it via dynamic import in vanilla mode. `any` is fine; we
// just need to silence the implicit-any error from tsc --strict.
declare module "frappe-gantt";
