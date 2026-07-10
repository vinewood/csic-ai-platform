import{F as e,R as t,d as n,lt as r,m as i,t as a}from"./_plugin-vue_export-helper-DefT6_p-.js";var o={class:`dify-embed-page`},s=[`src`],c=a({__name:`Chat`,setup(a){let c=r(null),l=r(`/dify/`);e(()=>{});function u(){try{let e=c.value;if(e&&e.contentDocument){let t=e.contentDocument.createElement(`style`);t.textContent=`
        /* 隐藏 Dify 顶部导航（我们有自己的一级导航） */
        header.h-full, nav.h-full, .ant-layout-sider { display: none !important; }
        main { margin-left: 0 !important; }
      `,e.contentDocument.head.appendChild(t)}}catch{}}return(e,r)=>(t(),i(`div`,o,[n(`iframe`,{ref_key:`difyFrame`,ref:c,src:l.value,class:`dify-frame`,frameborder:`0`,allow:`clipboard-read; clipboard-write`,onLoad:u},null,40,s)]))}},[[`__scopeId`,`data-v-cef9b671`]]);export{c as default};