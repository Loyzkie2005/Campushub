/* Presentation only: callers report confirmed outcomes, never inferred fetch success. */
(function () {
    'use strict';
    function initialize() {
    if (window.CampusHubAlerts) return;
    const types = new Set(['success','error','warning','info']);
    const root = document.createElement('div');
    root.className='admin-alert-region';root.id='adminAlertRegion';root.dataset.adminAlertRegion='true';
    root.setAttribute('role','region');root.setAttribute('aria-label','Action notifications');document.body.append(root);
    document.body.classList.add('has-admin-alerts');
    const actor=document.querySelector('[data-admin-user-id]')?.dataset.adminUserId;
    const storageKey=actor?`campushubAdminAlert:${actor}`:null;
    const check='<path stroke-linecap="round" stroke-linejoin="round" d="m9 12 2 2 4-4"/><circle cx="12" cy="12" r="9"/>';
    const warning='<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v5m0 3h.01M10.3 3.8 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0Z"/>';
    const info='<circle cx="12" cy="12" r="9"/><path stroke-linecap="round" d="M12 11v5m0-9h.01"/>';
    const active=new Map();
    function show(message,{type='success'}={}) {
        message=String(message||'').trim();if(!message) return;
        if(!types.has(type)) type='info';
        // Repeated feedback for one operation replaces its timer, not its card.
        for(const [node,entry] of active) if(entry.message===message&&entry.type===type){entry.reset();return node;}
        while(active.size>=3) active.values().next().value.dismiss(true);
        const card=document.createElement('div');card.className=`admin-alert admin-alert--${type}`;
        card.setAttribute('role',type==='error'?'alert':'status');card.setAttribute('aria-atomic','true');
        card.innerHTML=`<svg class="admin-alert__icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">${type==='success'?check:type==='info'?info:warning}</svg><div class="admin-alert__content"><strong class="admin-alert__title"></strong><p class="admin-alert__message"></p></div><button type="button" class="admin-alert__close" aria-label="Dismiss notification">&times;</button>`;
        card.querySelector('.admin-alert__title').textContent=({success:'Success',error:'Action needed',warning:'Please check',info:'Notice'})[type];
        card.querySelector('.admin-alert__message').textContent=message;
        const duration=type==='error'?6000:4500;
        let timer,deadline=Date.now()+duration,remaining=duration;
        function dismiss(immediate=false){clearTimeout(timer);active.delete(card);card.classList.remove('is-visible');card.inert=true;
            if(immediate)card.remove();else setTimeout(()=>card.remove(),200);}
        function resume(){if(card.matches(':hover')||card.contains(document.activeElement))return;clearTimeout(timer);deadline=Date.now()+remaining;timer=setTimeout(()=>dismiss(),remaining);}
        function pause(){clearTimeout(timer);remaining=Math.max(0,deadline-Date.now());}
        function reset(){remaining=duration;resume();}
        card.addEventListener('mouseenter',pause);card.addEventListener('mouseleave',resume);
        card.addEventListener('focusin',pause);card.addEventListener('focusout',()=>setTimeout(resume,0));
        card.querySelector('button').addEventListener('click',()=>dismiss());
        active.set(card,{message,type,dismiss,reset});root.append(card);
        requestAnimationFrame(()=>{if(card.isConnected)card.classList.add('is-visible');});reset();return card;
    }
    function remember(message,type='success') {
        if(!storageKey||!message)return;
        try{sessionStorage.setItem(storageKey,JSON.stringify({message:String(message),type,at:Date.now()}));}catch(_){}
    }
    window.CampusHubAlerts={show,success:message=>show(message),error:message=>show(message,{type:'error'}),info:message=>show(message,{type:'info'}),remember};
    document.addEventListener('campushub:notify',event=>show(event.detail?.message,{type:event.detail?.type}));
    document.querySelectorAll('[data-admin-flash]').forEach(node=>{
        const tags=(node.dataset.alertType||'').split(/\s+/);const type=['error','warning','success','info'].find(value=>tags.includes(value))||'info';
        show(node.textContent,{type});node.hidden=true;
    });
    // Adapt existing module toast emitters; observe only feedback nodes, not every
    // table/fetch operation. Cached module scripts still work with this renderer.
    const legacySelector='.campushub-toast,.product-save-toast,.facility-save-toast,.order-action-toast,.bk-toast';
    document.querySelectorAll(legacySelector).forEach(node=>{
        function forward(){
            if(!['show','is-show','is-visible'].some(value=>node.classList.contains(value)))return;
            const type=node.classList.contains('is-error')||node.classList.contains('toast-error')?'error':
                node.classList.contains('toast-info')?'info':node.classList.contains('toast-warning')?'warning':
                node.classList.contains('campushub-toast')&&!node.classList.contains('toast-success')?'info':'success';
            show(node.textContent,{type});
        }
        forward();new MutationObserver(forward).observe(node,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
    });
    if(storageKey)try{const raw=sessionStorage.getItem(storageKey);sessionStorage.removeItem(storageKey);
        if(raw){const queued=JSON.parse(raw);if(typeof queued.message==='string'&&Date.now()-queued.at>=0&&Date.now()-queued.at<30000)show(queued.message,{type:queued.type});}
    }catch(_){}
    }
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
    else initialize();
})();
