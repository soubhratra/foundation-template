import { ProfileClient } from "./profile-client";

import {
  readChannelPreferencesFromCookies,
  updateNotificationAction,
  updateProfileAction,
} from "@/actions/profile-actions";
import { getServerApi } from "@/lib/api/server";

export default async function ProfilePage() {
  const api = await getServerApi();
  const [user, channelPrefs] = await Promise.all([
    api.getCurrentUser(),
    readChannelPreferencesFromCookies(),
  ]);

  return (
    <ProfileClient
      user={user}
      channelPrefs={channelPrefs}
      updateProfileAction={updateProfileAction}
      updateNotificationAction={updateNotificationAction}
    />
  );
}
