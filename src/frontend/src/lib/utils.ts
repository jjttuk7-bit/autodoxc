import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** shadcn 표준 className 병합 — clsx로 조합 → tailwind-merge로 중복 해소. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
