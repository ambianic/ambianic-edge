import 'bootstrap/dist/css/bootstrap.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import App from './App.vue';
import InfiniteLoading from 'vue-infinite-loading';
import router from './router';

Vue.use(InfiniteLoading, { /* options */
  slots: {
    // keep default styles
    noResults: 'No data available on your timeline yet.',
    noMore: 'End of your timeline archive.',
  },
});

Vue.use(BootstrapVue);

Vue.config.productionTip = false;

new Vue({
  router,
  render: h => h(App),
}).$mount('#app');
