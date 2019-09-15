// vue.config.js
module.exports = {
  publicPath: './',
  devServer: {
    port: 1234,
  },

// if prod and dev app url differ
//  publicPath: process.env.NODE_ENV === 'production'
//    ? '/production-sub-path/'
  // options...
};
