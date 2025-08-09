// Enable asset loading for wasm used by expo-sqlite web
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Support loading .wasm (wa-sqlite) and .cjs
config.resolver.assetExts = [...config.resolver.assetExts, 'wasm'];
config.resolver.sourceExts = [...config.resolver.sourceExts, 'cjs'];

module.exports = config;


