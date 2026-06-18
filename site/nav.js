(function () {

  // Work whether the page is opened directly as a file (file://) or served
  // by a web server. Under file:// a leading "/" points at the drive root,
  // which breaks every link, so we build relative paths with a depth-aware
  // prefix instead of absolute "/..." paths.
  var rawPath = window.location.pathname.replace(/\\/g, '/');
  var divisions = ['intelligence', 'revenue', 'ops'];
  var activeDivision = '';
  for (var d = 0; d < divisions.length; d++) {
    if (rawPath.indexOf('/' + divisions[d] + '/') !== -1) {
      activeDivision = divisions[d];
      break;
    }
  }
  // Division pages live one folder deep; the homepage/root pages do not.
  var prefix = activeDivision ? '../' : '';

  // Turn a root-relative "/foo/bar.html" into a path that resolves correctly
  // from the current page in both file:// and served contexts.
  function rel(href) {
    return prefix + href.replace(/^\//, '');
  }

  var menus = {
    intelligence: {
      label: 'Intelligence',
      href: '/intelligence/index.html',
      items: [
        { name: 'Clarity Report',        href: '/index.html'                   },
        { name: 'Auto Ledger',           href: '/intelligence/vericount.html'  },
        { name: 'Rate Watch',            href: '/intelligence/oryn.html'       },
        { name: 'Rival Scan',            href: '/intelligence/veris.html'      },
        { name: 'Shift Lens',            href: '/intelligence/strata.html'     },
      ]
    },
    revenue: {
      label: 'Revenue',
      href: '/revenue/index.html',
      items: [
        { name: 'Call Catch',            href: '/revenue/missedcall.html'                   },
        { name: 'Quote Revive',          href: '/revenue/quoterevive.html'     },
        { name: 'Clear Ledger',          href: '/revenue/clearledger.html'     },
      ]
    },
    ops: {
      label: 'Ops',
      href: '/ops/index.html',
      items: [
        { name: 'Call Router',           href: '/ops/traderelay.html'          },
        { name: 'Permit Watch',          href: '/ops/permitwatch.html'         },
        { name: 'Crew Hire',             href: '/ops/ironhire.html'            },
        { name: 'Bay Coach',             href: '/ops/baysignal.html'           },
        { name: 'Drive Pay',             href: '/ops/hydropay.html'                         },
      ]
    }
  };

  function buildMenu(key) {
    var m = menus[key];
    var active = activeDivision === key;
    var items = m.items.map(function (item) {
      return '<a href="' + rel(item.href) + '" class="ef-dd-item">' + item.name + '</a>';
    }).join('');
    return '<div class="ef-dd-wrap">'
      + '<a href="' + rel(m.href) + '" class="ef-dd-trigger' + (active ? ' is-active' : '') + '">'
      + m.label + ' <span class="ef-caret">&#9662;</span>'
      + '</a>'
      + '<div class="ef-dd-panel">'
      + '<div class="ef-dd-head">' + m.label + '</div>'
      + items
      + '<a href="' + rel(m.href) + '" class="ef-dd-all">All ' + m.label + ' products &rarr;</a>'
      + '</div>'
      + '</div>';
  }

  var css = [
    '.ef-nav{padding:18px 0;border-bottom:1px solid #E5E7EB;background:#fff;position:relative;z-index:200;box-shadow:0 1px 4px rgba(10,39,79,0.08)}',
    '.ef-nav-inner{max-width:1080px;margin:0 auto;padding:0 24px;display:flex;justify-content:space-between;align-items:center}',
    '.ef-brand{display:flex;align-items:center;gap:12px;font-weight:700;color:#0A274F;font-size:22px;letter-spacing:-0.015em;text-decoration:none;font-family:Inter,-apple-system,sans-serif}',
    '.ef-brand:hover{text-decoration:none;color:#0A274F}',
    '.ef-brand-logo{width:48px;height:48px;background:#0A274F;border-radius:10px;display:flex;align-items:center;justify-content:center;overflow:hidden;flex-shrink:0}',
    '.ef-brand-logo img{width:100%;height:100%;object-fit:cover;display:block}',
    '.ef-nav-right{display:flex;align-items:center;gap:4px;flex-wrap:wrap}',
    /* dropdown wrapper */
    '.ef-dd-wrap{position:relative}',
    /* trigger link */
    '.ef-dd-trigger{display:flex;align-items:center;gap:5px;padding:8px 12px;border-radius:8px;font-size:15px;font-weight:500;color:#0A274F;font-family:Inter,-apple-system,sans-serif;text-decoration:none;white-space:nowrap;transition:background .12s,color .12s}',
    '.ef-dd-trigger:hover{background:#F9FAFB;color:#94681C;text-decoration:none}',
    '.ef-dd-trigger.is-active{color:#94681C}',
    '.ef-caret{font-size:10px;line-height:1;transition:transform .15s;display:inline-block;margin-top:1px}',
    /* panel — hidden by default, shown on hover */
    '.ef-dd-panel{display:none;position:absolute;top:calc(100% + 8px);right:0;min-width:240px;background:#fff;border:1px solid #E5E7EB;border-radius:14px;padding:8px;box-shadow:0 12px 36px rgba(10,39,79,.12);z-index:400}',
    '.ef-dd-wrap:hover .ef-dd-panel{display:block}',
    '.ef-dd-wrap:hover .ef-caret{transform:rotate(180deg)}',
    '.ef-dd-head{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#94681C;padding:6px 12px 8px;font-family:Inter,-apple-system,sans-serif}',
    '.ef-dd-item{display:flex;align-items:center;gap:8px;padding:10px 12px;font-size:14px;font-weight:500;color:#111827;border-radius:8px;text-decoration:none;font-family:Inter,-apple-system,sans-serif;transition:background .1s}',
    '.ef-dd-item:hover{background:#F9FAFB;color:#0A274F;text-decoration:none}',
    '.ef-dd-all{display:block;padding:10px 12px;font-size:13px;font-weight:600;color:#94681C;border-top:1px solid #E5E7EB;margin-top:4px;text-decoration:none;font-family:Inter,-apple-system,sans-serif;border-radius:0 0 8px 8px}',
    '.ef-dd-all:hover{background:#FDF3E3;text-decoration:none}',
    /* log in link — outlined secondary, sits left of the Talk to us CTA */
    '.ef-login{font-size:14px;font-weight:600;color:#0A274F;background:#fff;text-decoration:none;margin-left:12px;padding:8px 15px;border-radius:8px;border:1px solid #D1D5DB;font-family:Inter,-apple-system,sans-serif;white-space:nowrap;transition:background .12s,color .12s,border-color .12s}',
    '.ef-login:hover{background:#F9FAFB;color:#94681C;border-color:#94681C;text-decoration:none}',
    /* talk link */
    '.ef-talk{font-size:14px;font-weight:600;color:#fff;background:#94681C;text-decoration:none;margin-left:10px;padding:9px 16px;border-radius:8px;font-family:Inter,-apple-system,sans-serif;white-space:nowrap}',
    '.ef-talk:hover{background:#7E5616;color:#fff;text-decoration:none}',
    /* mobile */
    '@media(max-width:760px){',
    '.ef-dd-panel{right:auto;left:0;min-width:200px}',
    '.ef-dd-trigger{padding:8px 8px;font-size:14px}',
    '.ef-login{margin-left:8px;padding:7px 11px;font-size:13px}',
    '.ef-talk{margin-left:8px;padding:8px 12px;font-size:13px}',
    '}'
  ].join('');

  var html = '<style>' + css + '</style>'
    + '<nav class="ef-nav"><div class="ef-nav-inner">'
    + '<a href="' + rel('/index.html') + '" class="ef-brand">'
    + '<span class="ef-brand-logo"><img src="' + rel('/echoframe_logo.png') + '" alt="EchoFrame"></span>'
    + 'EchoFrame</a>'
    + '<div class="ef-nav-right">'
    + buildMenu('intelligence')
    + buildMenu('revenue')
    + buildMenu('ops')
    + '<a href="' + rel('/login.html') + '" class="ef-login">Log in</a>'
    + '<a href="mailto:jacobstarling4313@gmail.com" class="ef-talk">Talk to us</a>'
    + '</div></div></nav>';

  var el = document.getElementById('ef-nav');
  if (el) { el.outerHTML = html; } else { document.body.insertAdjacentHTML('afterbegin', html); }

})();
