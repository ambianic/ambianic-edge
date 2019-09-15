import 'bootstrap/dist/css/bootstrap.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import App from './App.vue';
import router from './router';
import InfiniteLoading from 'vue-infinite-loading';

export default Object.freeze({
  API_ROOT: '/api/',
});


Vue.use(InfiniteLoading, { /* options */ });

Vue.use(BootstrapVue);

Vue.config.productionTip = false;

new Vue({
  router,
  render: h => h(App),
}).$mount('#app');
