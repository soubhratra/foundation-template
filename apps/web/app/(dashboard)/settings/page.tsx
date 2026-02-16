import { SettingsClient } from "./settings-client";

import {
  changePasswordAction,
  readAlertPreferencesFromCookies,
  updateNotificationAction,
} from "@/actions/profile-actions";

export default async function SettingsPage() {
  const alertPrefs = await readAlertPreferencesFromCookies();

  return (
    <SettingsClient
      alertPrefs={alertPrefs}
      changePasswordAction={changePasswordAction}
      updateNotificationAction={updateNotificationAction}
    />
  );
}
