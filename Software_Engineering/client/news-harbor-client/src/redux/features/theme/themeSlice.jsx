import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  isDarkMode: true,
};

export const themeSlice = createSlice({
  name: "isDarkMode",
  initialState,
  reducers: {
    toggle: (state) => {
      state.isDarkMode = !state.isDarkMode;
    },
  },
});

export const { toggle } = themeSlice.actions;

export default themeSlice.reducer;
