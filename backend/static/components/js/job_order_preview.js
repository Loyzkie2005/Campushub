/* The DOCX-derived PDF is rendered as plain paper; export/Print keep its bytes. */
(function () {
    'use strict';
    const assets=new URL('../../vendor/pdfjs/6.4.299/',document.currentScript.src);
    const states=new Map();
    let library;
    function pdfLibrary() {
        if(!library) library=import(new URL('build/pdf.mjs',assets).href).then(pdf=>{
            pdf.GlobalWorkerOptions.workerSrc=new URL('build/pdf.worker.mjs',assets).href;
            return pdf;
        }).catch(error=>{library=null;throw error;});
        return library;
    }
    function release(state) {
        state.controller.abort();state.renderTask?.cancel();
        state.loadingTask?.destroy().catch(()=>{});
        state.frame?.remove();
        if(state.url) URL.revokeObjectURL(state.url);
    }
    function dispose() {states.forEach(release);states.clear();}
    function prepare(host) {
        if(!host) return null;
        if(states.has(host)) return states.get(host);
        const state={controller:new AbortController(),errorMessage:'Unable to display Job Order. Retry, or use Export.'};
        states.set(host,state);
        const file=async()=>{
            const response=await fetch(host.dataset.pdfUrl,{credentials:'same-origin',signal:state.controller.signal});
            if(!response.ok) {
                const result=await response.json().catch(()=>({}));
                state.errorMessage=result.error || 'Unable to load Job Order. Please retry.';
                throw new Error(state.errorMessage);
            }
            if(!response.headers.get('Content-Type')?.startsWith('application/pdf')) {
                state.errorMessage='Unable to load Job Order. Please sign in again.';
                throw new Error(state.errorMessage);
            }
            return response.blob();
        };
        // Begin on Overview, without rendering a hidden canvas or blocking navigation.
        state.ready=Promise.all([file(),pdfLibrary()]);
        state.ready.catch(()=>{}); // A later load shows the normal error/Retry state.
        return state;
    }
    async function load(host) {
        const state=prepare(host);
        if(!state || state.loading) return;
        state.loading=true;
        const active=()=>!state.controller.signal.aborted && host.isConnected;
        const printButton=host.parentElement.querySelector('[data-job-print]');
        if(printButton) printButton.disabled=true;
        host.setAttribute('aria-busy','true');
        const message=document.createElement('p');message.setAttribute('role','status');
        message.textContent='Preparing document...';host.replaceChildren(message);
        try {
            const [blob,pdf]=await state.ready;
            const data=new Uint8Array(await blob.arrayBuffer());
            if(!active()) return;
            state.url=URL.createObjectURL(blob);
            state.loadingTask=pdf.getDocument({data,
                standardFontDataUrl:new URL('standard_fonts/',assets).href,
                wasmUrl:new URL('wasm/',assets).href,isEvalSupported:false});
            const documentPDF=await state.loadingTask.promise;
            if(!active()) return;
            const pages=document.createElement('div');pages.className='beu-job-pages';
            host.replaceChildren(pages,message);
            for(let index=1;index<=documentPDF.numPages;index++) {
                const page=await documentPDF.getPage(index);
                if(!active()) return;
                const viewport=page.getViewport({scale:1});
                const width=Math.min(host.clientWidth || 794,794);
                const scale=width/viewport.width*Math.min(window.devicePixelRatio || 1,2);
                const renderViewport=page.getViewport({scale});
                const paper=document.createElement('section');paper.className='beu-job-paper';
                paper.setAttribute('aria-label',`Job Order page ${index} of ${documentPDF.numPages}`);
                const canvas=document.createElement('canvas');canvas.setAttribute('aria-hidden','true');
                canvas.width=Math.ceil(renderViewport.width);canvas.height=Math.ceil(renderViewport.height);
                state.renderTask=page.render({canvasContext:canvas.getContext('2d'),viewport:renderViewport});
                await state.renderTask.promise;state.renderTask=null;
                if(!active()) return;
                // Show completed pages immediately instead of waiting for the last one.
                paper.append(canvas);pages.append(paper);message.remove();
                if(printButton) printButton.disabled=false;
                const content=await page.getTextContent();
                const text=document.createElement('div');text.className='beu-job-paper-text';
                text.textContent=content.items.map(item=>item.str || '').join(' ');
                paper.append(text);
            }
            if(!active()) return;
            host.removeAttribute('aria-busy');
            if(printButton) printButton.disabled=false;
        } catch(error) {
            if(!active()) return;
            if(printButton) printButton.disabled=true;
            release(state);states.delete(host);message.textContent=state.errorMessage;
            const retry=document.createElement('button');retry.type='button';retry.textContent='Retry';
            retry.addEventListener('click',()=>load(host));host.replaceChildren(message,retry);
            host.removeAttribute('aria-busy');
        }
    }
    function print(host) {
        const state=states.get(host);
        if(!state?.url) return;
        const launch=()=>{
            try {state.frame.contentWindow.focus();state.frame.contentWindow.print();}
            catch(error) {window.open(state.url,'_blank','noopener');}
        };
        if(state.frame) {if(state.printReady) launch();return;}
        const frame=document.createElement('iframe');frame.className='beu-job-print-frame';
        frame.title='Print Job Order';frame.setAttribute('aria-hidden','true');frame.tabIndex=-1;
        frame.addEventListener('load',()=>{state.printReady=true;launch();},{once:true});frame.src=state.url;state.frame=frame;
        document.body.append(frame);
    }
    function exportMenu(pdfUrl,docxUrl) {
        const menu=document.createElement('details');menu.className='beu-job-export';
        const summary=document.createElement('summary');summary.setAttribute('aria-label','Export Job Order');
        summary.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12m-4-4 4 4 4-4M5 17v4h14v-4"/></svg><span>Export</span><svg class="beu-export-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
        const options=document.createElement('div');options.className='beu-job-export-options';
        for(const [label,url] of [['PDF (.pdf)',pdfUrl],['Word (.docx)',docxUrl]]) {
            const link=document.createElement('a');link.textContent=label;link.href=url;options.append(link);
        }
        menu.append(summary,options);return menu.outerHTML;
    }
    document.addEventListener('click',event=>{
        document.querySelectorAll('.beu-job-export[open]').forEach(menu=>{
            if(!menu.contains(event.target) || event.target.closest('a')) menu.open=false;
        });
    });
    document.addEventListener('keydown',event=>{
        if(event.key!=='Escape') return;
        const menu=document.querySelector('.beu-job-export[open]');
        if(menu) {event.preventDefault();menu.open=false;menu.querySelector('summary').focus();}
    });
    window.CampusHubJobOrder={prepare,load,print,dispose,exportMenu};
    window.addEventListener('pagehide',dispose);
    window.addEventListener('pageshow',event=>{
        if(event.persisted) document.querySelectorAll('[data-job-preview]').forEach(host=>{if(host.getClientRects().length) load(host);});
    });
    const standalone=document.querySelector('[data-job-order-standalone]');
    if(standalone) {
        const exports=standalone.querySelector('[data-job-export]');
        exports.outerHTML=exportMenu(exports.dataset.pdfUrl,exports.dataset.docxUrl);
        const host=standalone.querySelector('[data-job-preview]');load(host);
        standalone.querySelector('[data-job-print]').addEventListener('click',()=>print(host));
    }
})();
