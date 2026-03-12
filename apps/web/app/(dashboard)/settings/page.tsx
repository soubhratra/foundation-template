import { SettingsClient } from "./settings-client";

import {
  changePasswordAction,
  readAlertPreferencesFromCookies,
  updateNotificationAction,
} from "@/actions/profile-actions";
import { deleteAccountAction } from "@/actions/account-actions";

export default async function SettingsPage() {
  const alertPrefs = await readAlertPreferencesFromCookies();

  return (
    <SettingsClient
      alertPrefs={alertPrefs}
      changePasswordAction={changePasswordAction}
      updateNotificationAction={updateNotificationAction}
      deleteAccountAction={deleteAccountAction}
    />
  );
}
