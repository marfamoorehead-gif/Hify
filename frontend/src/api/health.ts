/*
 * @Author: 汪培良 rick_wang@yunquna.com
 * @Date: 2026-05-04 14:47:29
 * @LastEditors: 汪培良 rick_wang@yunquna.com
 * @LastEditTime: 2026-05-04 19:25:11
 * @FilePath: /Hify/frontend/src/api/health.ts
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import { get } from "@/utils/request";

export function getHealth() {
  return get<{ status: string }>("/health");
}
