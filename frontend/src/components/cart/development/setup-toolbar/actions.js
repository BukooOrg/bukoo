"use server";







export async function checkEnvironmentVariables()


{
  // Only check environment variables in development
  if (process.env.NODE_ENV === "production") {
    return {
      envs: [],
      allValid: true
    };
  }

  const requiredEnvs = [
  { name: "SFCC_CLIENT_ID", label: "SFCC Client ID" },
  { name: "SFCC_ORGANIZATIONID", label: "SFCC Organization ID" },
  { name: "SFCC_SECRET", label: "SFCC Secret" },
  { name: "SFCC_SHORTCODE", label: "SFCC Short Code" },
  { name: "SFCC_SITEID", label: "SFCC Site ID" },
  { name: "SITE_NAME", label: "Site Name" },
  { name: "SFCC_REVALIDATION_SECRET", label: "SFCC Revalidation Secret" }];


  const envs = requiredEnvs.map((env) => ({
    name: env.name,
    label: env.label,
    isValid: Boolean(process.env[env.name])
  }));

  const allValid = envs.every((env) => env.isValid);

  return {
    envs,
    allValid
  };
}
