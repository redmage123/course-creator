/**
 * User State Slice
 *
 * BUSINESS CONTEXT:
 * Manages current user profile data including personal information, preferences,
 * and organization membership.
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { UserRole } from './authSlice';

interface UserProfile {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: UserRole;
  organizationId?: string;
  organizationName?: string;
  avatar?: string;
  preferences?: Record<string, unknown>;
}

interface UserState {
  profile: UserProfile | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: UserState = {
  profile: null,
  isLoading: false,
  error: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setUserProfile: (state, action: PayloadAction<UserProfile>) => {
      state.profile = action.payload;
      state.error = null;
    },

    updateUserProfile: (state, action: PayloadAction<Partial<UserProfile>>) => {
      if (state.profile) {
        state.profile = { ...state.profile, ...action.payload };
      }
    },

    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },

    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.isLoading = false;
    },

    clearUser: (state) => {
      state.profile = null;
      state.error = null;
      state.isLoading = false;
    },
  },
});

export const { setUserProfile, updateUserProfile, setLoading, setError, clearUser } =
  userSlice.actions;

export default userSlice.reducer;
