<template>
  <div id="app">
    <header class="hacker-news-header">
      <a target="_blank" href="http://www.ycombinator.com/">
        <img src="https://news.ycombinator.com/y18.gif">
      </a>
      <span>Hacker News</span>
      <select v-model="newsType" @change="changeType()">
          <option value="story">Story</option>
          <option value="poll">Poll</option>
          <option value="show_hn">Show hn</option>
          <option value="ask_hn">Ask hn</option>
          <option value="front_page">Front page</option>
      </select>
    </header>
    <div
      class="hacker-news-item"
      v-for="(item, $index) in list"
      :key="$index"
      :data-num="$index + 1">
      <a target="_blank" :href="item.url" v-text="item.title"></a>
      <p>
        <span v-text="item.points"></span>
        points by
        <a
          target="_blank"
          :href="`https://news.ycombinator.com/user?id=${item.author}`"
          v-text="item.author"></a>
        |
        <a
          target="_blank"
          :href="`https://news.ycombinator.com/item?id=${item.objectID}`"
          v-text="`${item.num_comments} comments`"></a>
      </p>
    </div>

    <infinite-loading :identifier="infiniteId" @infinite="infiniteHandler"></infinite-loading>
  </div>
</template>

<script>
//import InfiniteLoading from 'vue-infinite-loading';
import axios from 'axios';

const api = 'http://hn.algolia.com/api/v1/search_by_date?tags=story';

export default {
  data() {
    return {
      page: 1,
      list: [],
      newsType: 'story',
      infiniteId: +new Date(),
    };
  },
//  components: {
//    InfiniteLoading,
//  },
  methods: {
    infiniteHandler($state) {
      axios.get(api, {
        params: {
          page: this.page,
          tags: this.newsType,
        },
      }).then(({ data }) => {
        if (data.hits.length) {
          this.page += 1;
          this.list.push(...data.hits);
          console.debug('this.list hacker news hits count: '+ JSON.stringify(this.list.length));
          $state.loaded();
        } else {
          $state.complete();
        }
      });
    },
    changeType() {
      this.page = 1;
      this.list = [];
      this.infiniteId += 1;
    },
  },
};

</script>
