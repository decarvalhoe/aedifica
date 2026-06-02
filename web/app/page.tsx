import { redirect } from "next/navigation";

// No marketing landing page — go straight to the working surface.
export default function Home() {
  redirect("/workspace");
}
