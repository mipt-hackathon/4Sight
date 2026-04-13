export const env = {
  backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:18000",
  mlApiUrl: process.env.NEXT_PUBLIC_ML_API_URL ?? "http://localhost:18001",
  backendInternalUrl:
    process.env.BACKEND_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_BACKEND_URL ??
    "http://backend:8000",
};
