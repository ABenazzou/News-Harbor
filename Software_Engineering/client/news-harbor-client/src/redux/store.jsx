import { configureStore, combineReducers  } from "@reduxjs/toolkit";
import themeReducer from "@/redux/features/theme/themeSlice";
import { persistStore, persistReducer } from "redux-persist";
import storage from "redux-persist/lib/storage";

const persistConfig = {
    key: 'root',
    storage,
};

const rootReducer = combineReducers({
    theme: themeReducer,
});
  
const persistedReducer = persistReducer(persistConfig, rootReducer)

export const store = configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoreActions: ['persist/PERSIST']
            }
        })
});

export const persistor = persistStore(store);