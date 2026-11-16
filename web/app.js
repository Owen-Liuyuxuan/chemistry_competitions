'use strict';
(() => {
  const $ = (selector) => document.querySelector(selector);
  const escape = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const safeUrl = (value) => {
    if (!value || /^(?:javascript|data|vbscript):/i.test(String(value))) return '';
    try { const url = new URL(String(value), location.href); return ['http:', 'https:', 'file:'].includes(url.protocol) ? escape(value) : ''; } catch { return ''; }
  };
  const labels = {
    downloaded:'已归档', available:'已获取', archived:'已归档', complete:'已归档', collected:'已获取',
    partial:'部分获取', missing:'尚未获取', not_found:'尚未获取', unavailable:'暂不可获取', fetch_failed:'获取失败',
    source_only:'仅来源索引', pending:'待核验', pending_review:'待核验', needs_review:'待复核',
    not_held:'未举办', cancelled:'已取消', postponed:'延期举办', not_published:'尚未发布', unpublished:'尚未发布',
    project_based:'项目型赛事', project:'项目型赛事', not_applicable:'不适用', not_annual:'非年度赛事', access_limited:'访问受限', located:'来源已定位', download_failed:'获取失败',
    verified:'已核验', reviewed:'已复核', auto:'自动提取，待复核', machine_checked:'程序校验',
    boundary_verified:'边界已核验', automatic:'自动提取，待复核', manual:'已人工标定'
  };
  const kindLabels = {problems:'试题',solutions:'参考答案',combined:'题目与答案',preparatory:'预备题',report:'赛事资料',rules:'赛事规则'};
  let data, resources, competitions;
  let view = 'papers', page = 1, currentQuestion = null, readerTab = 'problem', paperFilter = '';
  let filtered = [], visibleQuestions = [];
  const pageSize = 24;
  const statusLabel = (value) => labels[value] || value || '待核验';
  const competitionName = (id) => competitions.get(id)?.name || id || '化学竞赛';
  const hasAnswer = (row) => view === 'papers' ? Boolean(row.solution_resource_id) : Boolean(row.solution);
  const resourceLink = (resource, label, className = '') => {
    const url = safeUrl(resource?.local_path);
    return url ? `<a class="button-link ${className}" href="${url}" target="_blank" rel="noopener">${escape(label)} ↗</a>` : '';
  };
  const sourceLink = (url, label = '原始来源') => {
    const safe = safeUrl(url);
    return safe ? `<a href="${safe}" target="_blank" rel="noopener noreferrer">${escape(label)} ↗</a>` : '';
  };
  const tagHtml = (tag, interactive = false) => interactive ? `<button class="tag tag-button" type="button" data-tag="${escape(tag)}">${escape(tag)}</button>` : `<span class="tag">${escape(tag)}</span>`;
  const getQuestionTags = (paper) => [...new Set((paper.question_ids || []).flatMap((id) => questionMap.get(id)?.tags || []))];
  let questionMap = new Map();

  function populateFilters() {
    const ids = [...new Set([...data.papers, ...data.questions, ...data.coverage].map((row) => row.competition).filter(Boolean))];
    $('#competition').innerHTML += ids.sort().map((id) => `<option value="${escape(id)}">${escape(competitionName(id))}</option>`).join('');
    const years = [...new Set([...data.papers, ...data.questions, ...data.coverage].map((row) => row.year).filter(Boolean))].sort((a,b) => b-a);
    $('#year').innerHTML += years.map((year) => `<option value="${escape(year)}">${escape(year)}</option>`).join('');
    const tags = [...new Set(data.questions.flatMap((row) => row.tags || []))].sort((a,b) => a.localeCompare(b,'zh-CN'));
    $('#tag').innerHTML += tags.map((tag) => `<option value="${escape(tag)}">${escape(tag)}</option>`).join('');
    const archived = data.resources.filter((row) => row.local_path).length;
    const paired = data.questions.filter((row) => row.solution).length;
    $('#stats').innerHTML = [[data.papers.length,'份卷与任务','整卷与开放项目独立建档'],[data.questions.length,'道题目','保留原页与题答关联'],[archived,'份原件','含题卷、答案和赛事资料'],[ids.length,'类竞赛',`${paired} 道题已关联参考答案`]].map(([number,label,note]) => `<div class="stat"><strong>${number.toLocaleString('zh-CN')}</strong><span>${label}</span><small>${escape(note)}</small></div>`).join('');
    for (const name of ['papers','questions','coverage']) $(`#${name}-count`).textContent = data[name].length.toLocaleString('zh-CN');
  }

  function queryRows() {
    const query = $('#search').value.trim().toLocaleLowerCase();
    const terms = query.split(/\s+/).filter(Boolean);
    const competition = $('#competition').value, year = $('#year').value, tag = $('#tag').value, answer = $('#answer').value;
    const rows = data[view].filter((row) => {
      if (competition && row.competition !== competition) return false;
      if (year && String(row.year) !== year) return false;
      if (view === 'questions' && paperFilter && row.paper_id !== paperFilter) return false;
      if (view !== 'coverage') {
        const tags = view === 'papers' ? getQuestionTags(row) : row.tags || [];
        if (tag && !tags.includes(tag)) return false;
        if (answer === 'paired' && !hasAnswer(row)) return false;
        if (answer === 'missing' && hasAnswer(row)) return false;
      }
      const searchText = [row.id,row.title,row.year,row.stage,row.competition,competitionName(row.competition),row.text_excerpt,row.notes,...(row.tags || []),...(view === 'papers' ? getQuestionTags(row) : []),statusLabel(row.status)].join(' ').toLocaleLowerCase();
      return terms.every((term) => searchText.includes(term));
    });
    const sort = $('#sort').value;
    rows.sort((a,b) => (sort === 'competition' ? competitionName(a.competition).localeCompare(competitionName(b.competition),'zh-CN') : 0) || (sort === 'oldest' ? (a.year || 0)-(b.year || 0) : (b.year || 0)-(a.year || 0)) || String(a.stage || '').localeCompare(String(b.stage || ''),'zh-CN') || (Number(a.number) || 0)-(Number(b.number) || 0) || String(a.id).localeCompare(String(b.id),undefined,{numeric:true}));
    return rows;
  }

  function paperCard(paper) {
    const problem = resources.get(paper.problem_resource_id), solution = resources.get(paper.solution_resource_id);
    const tags = getQuestionTags(paper).slice(0,5);
    const count = (paper.question_ids || []).length;
    return `<article class="paper-card"><div class="paper-year">${escape(paper.year)}<small>ARCHIVE</small></div><div><p class="card-kicker">${escape(competitionName(paper.competition))} · ${escape(paper.stage)}</p><h3>${escape(paper.title)}</h3><div class="paper-meta"><span>${count ? `${count} 道独立题目` : '逐题切分待补充'}</span><span>${problem?.pages ? `${problem.pages} 页原卷` : statusLabel(problem?.status)}</span><span>${paper.solution_resource_id ? '已关联参考答案' : (paper.format === 'open_project' ? '开放任务，无唯一答案' : '参考答案待补充')}</span></div>${tags.length ? `<div class="tags">${tags.map((tag) => tagHtml(tag,true)).join('')}</div>` : ''}${paper.notes ? `<p class="card-note">${escape(paper.notes)}</p>` : ''}</div><div class="paper-actions">${resourceLink(problem,'打开试题原卷','primary')}${solution && solution.id !== problem?.id ? resourceLink(solution,'参考答案原卷') : ''}${count ? `<button type="button" data-paper="${escape(paper.id)}">浏览本卷 ${count} 道题 →</button>` : ''}<div class="source-links">${sourceLink(problem?.landing_url || problem?.source_url)}${solution && solution.id !== problem?.id ? sourceLink(solution.landing_url || solution.source_url,'答案来源') : ''}</div></div></article>`;
  }

  function questionCard(question) {
    return `<article class="question-card"><div class="question-top"><span>${escape(question.competition)} / ${escape(question.year)} / ${escape(question.stage)}</span><span class="question-number">${escape(question.number)}</span></div><h3><button type="button" data-question="${escape(question.id)}">${escape(question.title || `第 ${question.number} 题`)}</button></h3>${question.excerpt_method === 'ocr' ? '<p class="excerpt">题面以原卷图像展示 · OCR 文本用于辅助检索</p>' : question.text_excerpt ? `<p class="excerpt">${escape(question.text_excerpt)}</p>` : ''}<div class="tags">${(question.tags || []).map((tag) => tagHtml(tag,true)).join('')}</div><div class="question-bottom"><span class="answer-status ${question.solution ? 'paired' : ''}">${question.solution ? '● 已关联答案' : question.format === 'open_project' ? '◇ 开放任务，无唯一答案' : '○ 答案待补充'}</span><button type="button" class="read-button" data-question="${escape(question.id)}">阅读原题 ↗</button></div></article>`;
  }

  function coverageCard(row) {
    const good = ['downloaded','available','complete','archived','collected','verified'].includes(row.status);
    return `<article class="coverage-card"><div class="paper-year">${escape(row.year || '—')}<small>SOURCE</small></div><div><h3>${escape(row.title || `${competitionName(row.competition)} · ${row.stage || ''}`)}</h3><p>${escape(row.notes || row.description || '等待补充来源核验记录。')}</p><div class="source-links">${sourceLink(row.source_url || row.landing_url)}${row.resource_id ? resourceLink(resources.get(row.resource_id),'归档资料') : ''}</div></div><span class="status-pill ${good ? 'good' : ''}">${escape(statusLabel(row.status))}</span></article>`;
  }

  function render() {
    filtered = queryRows();
    if (view === 'questions') visibleQuestions = filtered;
    const pages = Math.max(1,Math.ceil(filtered.length/pageSize));
    page = Math.max(1,Math.min(page,pages));
    const begin = (page-1)*pageSize, rows = filtered.slice(begin,begin+pageSize);
    $('#results').className = view === 'questions' ? 'results question-grid' : 'results';
    $('#results').setAttribute('aria-busy','false');
    const coverageIntro = view === 'coverage' ? '<p class="coverage-intro">覆盖记录描述实际采集结果。“尚未获取”表示仍缺资料；“未举办”表示该年没有该场考试；项目型赛事按规则、任务与作品资料建索引。年份按赛事举办年记录，期刊发表年份可能不同。</p>' : '';
    $('#results').innerHTML = coverageIntro + (rows.length ? rows.map(view === 'papers' ? paperCard : view === 'questions' ? questionCard : coverageCard).join('') : '<div class="empty"><h3>没有符合筛选条件的资料</h3><p>试试减少条件，或切换到覆盖与调研查看缺口记录。</p><button class="text-button" type="button" data-reset>重置筛选 →</button></div>');
    const noun = view === 'papers' ? '份卷与任务' : view === 'questions' ? '道题目' : '条记录';
    $('#result-summary').textContent = `找到 ${filtered.length.toLocaleString('zh-CN')} ${noun}`;
    $('#active-description').textContent = paperFilter && view === 'questions' ? `仅显示本卷题目 · ${data.papers.find((row) => row.id === paperFilter)?.title || paperFilter}` : view === 'papers' ? '按年份浏览竞赛整卷' : view === 'questions' ? '按化学主题探索独立题目' : '资料可获取状态与赛事范围';
    $('#pagination').innerHTML = filtered.length > pageSize ? `<button type="button" data-page="${page-1}" ${page===1 ? 'disabled' : ''}>← 上一页</button><span>第 ${page} / ${pages} 页</span><button type="button" data-page="${page+1}" ${page===pages ? 'disabled' : ''}>下一页 →</button>` : '';
    for (const link of document.querySelectorAll('[data-view]')) {
      const active = link.dataset.view === view;
      link.classList.toggle('active',active);
      if (active) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
    }
    $('#tag-filter').hidden = view === 'coverage';
    $('#answer-filter').hidden = view === 'coverage';
  }

  function resetFilters() {
    for (const id of ['search','competition','year','tag','answer']) $(`#${id}`).value = '';
    $('#sort').value = 'newest';
    paperFilter = ''; page = 1;
    if (location.hash.startsWith('#questions?')) history.replaceState(null,'','#questions');
    render();
  }

  function renderReader() {
    const question = currentQuestion;
    if (!question) return;
    $('#reader-meta').textContent = `${competitionName(question.competition)} · ${question.year} · ${question.stage} · 第 ${question.number} 题`;
    $('#reader-title').textContent = question.title || `第 ${question.number} 题`;
    $('#reader-tags').innerHTML = (question.tags || []).map((tag) => tagHtml(tag)).join('');
    $('#reader-status').textContent = `切分状态：${statusLabel(question.review_status)}${question.notes ? ' · '+question.notes : ''}`;
    for (const button of document.querySelectorAll('[data-reader-tab]')) {
      const active = button.dataset.readerTab === readerTab;
      button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));
    }
    const block = question[readerTab], resource = resources.get(block?.resource_id);
    const segments = block?.segments || [];
    if (!block) {
      $('#reader-body').innerHTML = '<div class="empty"><h3>尚未关联参考答案</h3><p>可先查阅本卷原件与来源记录，后续补充的答案将在此处关联。</p></div>';
    } else {
      let header = `<div class="reader-info"><span>来源：${escape(resource?.authority || '见原始来源')}</span>${resource?.local_path ? `<a href="${safeUrl(resource.local_path)}#page=${Number(segments[0]?.page) || 1}" target="_blank" rel="noopener">打开整卷 ↗</a>` : ''}${sourceLink(resource?.landing_url || resource?.source_url)}<span>${escape(kindLabels[resource?.kind] || '')}</span></div>`;
      if (resource?.notes) header += `<p class="reader-note">${escape(resource.notes)}</p>`;
      if (segments.length) {
        header += segments.map((segment,index) => {
          const image = safeUrl(segment.image);
          const pageNumber = segment.page ?? '—';
          return `<figure class="segment"><figcaption>原卷第 ${escape(pageNumber)} 页 · 分片 ${index+1}/${segments.length}${image ? ` · <a href="${image}" target="_blank" rel="noopener">查看原尺寸 ↗</a>` : ''}</figcaption>${image ? `<a href="${image}" target="_blank" rel="noopener" aria-label="查看第 ${escape(pageNumber)} 页分片原图"><img src="${image}" alt="${escape(question.title || `第 ${question.number} 题`)} · ${readerTab === 'problem' ? '题目' : '参考答案'} · 原卷第 ${escape(pageNumber)} 页" loading="${index ? 'lazy' : 'eager'}"></a>` : '<p class="reader-note">此分片图像待生成，请打开整卷查看。</p>'}</figure>`;
        }).join('');
      } else header += '<div class="empty"><h3>分片图像待补充</h3><p>请通过上方入口打开整卷原件。</p></div>';
      $('#reader-body').innerHTML = header;
    }
    const sequence = visibleQuestions.length && visibleQuestions.some((row) => row.id === question.id) ? visibleQuestions : data.questions;
    const index = sequence.findIndex((row) => row.id === question.id);
    $('#previous-question').disabled = index <= 0;
    $('#next-question').disabled = index < 0 || index >= sequence.length-1;
  }

  function openQuestion(id) {
    const question = questionMap.get(id);
    if (!question) return;
    currentQuestion = question;readerTab = 'problem';renderReader();
    if (!$('#reader').open) $('#reader').showModal();
    $('#reader').scrollTop = 0;
  }

  function closeReader() {
    if ($('#reader').open) $('#reader').close();
    currentQuestion = null;
    if (location.hash.startsWith('#question/')) history.replaceState(null,'',`#${view}${paperFilter && view === 'questions' ? '?paper='+encodeURIComponent(paperFilter) : ''}`);
  }

  function handleRoute() {
    const hash = location.hash.slice(1);
    if (hash.startsWith('question/')) {
      let id;
      try { id = decodeURIComponent(hash.slice(9)); } catch { id = ''; }
      if (questionMap.has(id)) { view = 'questions';render();openQuestion(id); }
      else { view = 'questions';render();$('#result-summary').textContent = '该题目链接未在当前目录中找到'; }
      return;
    }
    const [name,query = ''] = hash.split('?');
    if (['papers','questions','coverage'].includes(name)) view = name;
    paperFilter = view === 'questions' ? new URLSearchParams(query).get('paper') || '' : '';
    page = 1;
    if ($('#reader').open) { $('#reader').close();currentQuestion = null; }
    render();
  }

  function nextQuestion(offset) {
    if (!currentQuestion) return;
    const sequence = visibleQuestions.length && visibleQuestions.some((row) => row.id === currentQuestion.id) ? visibleQuestions : data.questions;
    const index = sequence.findIndex((row) => row.id === currentQuestion.id);
    const next = sequence[index+offset];
    if (next) location.hash = `question/${encodeURIComponent(next.id)}`;
  }

  async function init() {
    try {
      const response = await fetch('data/catalog.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      data = await response.json();
      for (const key of ['resources','papers','questions','coverage','competitions']) if (!Array.isArray(data[key])) data[key] = [];
      resources = new Map(data.resources.map((row) => [row.id,row]));
      competitions = new Map(data.competitions.map((row) => [row.id,row]));
      questionMap = new Map(data.questions.map((row) => [row.id,row]));
      populateFilters();handleRoute();
      $('#filters').addEventListener('submit',(event) => event.preventDefault());
      let timer;
      $('#search').addEventListener('input',() => { clearTimeout(timer);timer=setTimeout(() => { page=1;render(); },150); });
      for (const id of ['competition','year','tag','answer','sort']) $(`#${id}`).addEventListener('change',() => { page=1;render(); });
      $('#reset').addEventListener('click',resetFilters);
      document.addEventListener('click',(event) => {
        const button = event.target.closest('[data-question],[data-paper],[data-tag],[data-page],[data-reset]');
        if (!button) return;
        if (button.dataset.question) location.hash = `question/${encodeURIComponent(button.dataset.question)}`;
        else if (button.dataset.paper) location.hash = `questions?paper=${encodeURIComponent(button.dataset.paper)}`;
        else if (button.dataset.tag) { $('#tag').value=button.dataset.tag;page=1;render(); }
        else if (button.hasAttribute('data-page')) { page=Number(button.dataset.page);render();$('.workspace-heading').scrollIntoView({behavior:'smooth',block:'start'}); }
        else if (button.hasAttribute('data-reset')) resetFilters();
      });
      window.addEventListener('hashchange',handleRoute);
      $('#close-reader').addEventListener('click',closeReader);
      $('#reader').addEventListener('cancel',(event) => { event.preventDefault();closeReader(); });
      $('#reader').addEventListener('click',(event) => { if(event.target === $('#reader')) { const bounds=$('#reader').getBoundingClientRect();if(event.clientX<bounds.left || event.clientX>bounds.right || event.clientY<bounds.top || event.clientY>bounds.bottom) closeReader(); } });
      for (const button of document.querySelectorAll('[data-reader-tab]')) button.addEventListener('click',() => { readerTab=button.dataset.readerTab;renderReader(); });
      $('#previous-question').addEventListener('click',() => nextQuestion(-1));
      $('#next-question').addEventListener('click',() => nextQuestion(1));
    } catch (error) {
      console.error('Could not load Chemistry Atlas catalog:',error);
      $('#results').setAttribute('aria-busy','false');
      $('#results').innerHTML='<div class="empty"><h3>目录暂时无法读取</h3><p>请确认 data/catalog.json 已随网页部署；本地浏览请通过静态 HTTP 服务器打开。</p><p><a href="data/catalog.json">直接打开资料索引 ↗</a></p></div>';
      $('#result-summary').textContent='目录读取失败';
    }
  }
  init();
})();
