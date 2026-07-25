;;; pages.el --- Org-roam publishing for StarIntel GPT Auto Dig -*- lexical-binding: t; -*-

(require 'cl-lib)
(require 'json)
(require 'org)
(require 'org-element)
(require 'org-id)
(require 'org-roam)
(require 'ox-html)
(require 'seq)
(require 'subr-x)
(require 'url-util)

(defgroup starintel-pages nil
  "Publish the StarIntel GPT auto-dig Org-roam graph."
  :group 'org)

(defcustom starintel-pages-site-title "StarIntel GPT Auto Dig"
  "Title shown in the generated site."
  :type 'string)

(defvar starintel-pages-root nil)
(defvar starintel-pages--stage nil)
(defvar starintel-pages--site nil)
(defvar starintel-pages--files nil)
(defvar starintel-pages--file-nodes nil)
(defvar starintel-pages--records nil)

(defun starintel-pages--root (&optional start)
  (or starintel-pages-root
      (file-name-as-directory
       (file-truename
        (or (locate-dominating-file (or start default-directory) "AGENTS.md")
            (error "Cannot locate repository root"))))))

(defun starintel-pages--org-files (directory)
  (sort (directory-files-recursively directory "\\.org\\'") #'string<))

(defun starintel-pages--keyword (file keyword)
  (with-temp-buffer
    (insert-file-contents file)
    (org-mode)
    (car (cdr (assoc-string
               (upcase keyword)
               (org-collect-keywords (list (upcase keyword)))
               t)))))

(defun starintel-pages--file-id (file)
  (with-temp-buffer
    (insert-file-contents file)
    (goto-char (point-min))
    (let ((limit (or (save-excursion (re-search-forward "^\\*+ " nil t))
                     (point-max))))
      (when (re-search-forward "^:ID:[ \t]+\\([^ \t\n]+\\)" limit t)
        (match-string-no-properties 1)))))

(defun starintel-pages--stable-id (relative)
  (format "starintel-gpt-%s" (substring (secure-hash 'sha256 relative) 0 32)))

(defun starintel-pages--ensure-id (file)
  (or (starintel-pages--file-id file)
      (let ((id (starintel-pages--stable-id
                 (file-relative-name file starintel-pages--stage))))
        (with-temp-buffer
          (insert-file-contents file)
          (goto-char (point-min))
          (insert ":PROPERTIES:\n:ID:       " id "\n:END:\n")
          (write-region (point-min) (point-max) file nil 'silent))
        id)))

(defun starintel-pages--prepare ()
  (let* ((root (starintel-pages--root))
         (source (expand-file-name "roam" root))
         (build (expand-file-name ".cache/pages" root)))
    (setq starintel-pages--stage (expand-file-name "roam" build)
          starintel-pages--site (expand-file-name "_site" root))
    (when (file-directory-p build) (delete-directory build t))
    (when (file-directory-p starintel-pages--site)
      (delete-directory starintel-pages--site t))
    (make-directory build t)
    (make-directory starintel-pages--site t)
    (copy-directory source starintel-pages--stage t t t)
    (setq starintel-pages--files (starintel-pages--org-files starintel-pages--stage))
    (dolist (file starintel-pages--files)
      (starintel-pages--ensure-id file))
    starintel-pages--files))

(defun starintel-pages--configure-roam ()
  (let ((build (file-name-directory (directory-file-name starintel-pages--stage))))
    (setq org-roam-directory (file-truename starintel-pages--stage)
          org-roam-db-location (expand-file-name "org-roam.db" build)
          org-id-locations-file (expand-file-name "org-id-locations" build)
          org-roam-db-update-on-save nil)
    (org-id-update-id-locations starintel-pages--files)
    (org-roam-db-sync)
    (setq starintel-pages--file-nodes (make-hash-table :test #'equal))
    (dolist (node (org-roam-node-list))
      (when (zerop (or (org-roam-node-level node) 0))
        (puthash (file-truename (org-roam-node-file node))
                 node starintel-pages--file-nodes)))))

(defun starintel-pages--output-file (file)
  (expand-file-name
   (concat "notes/"
           (file-name-sans-extension
            (file-relative-name file starintel-pages--stage))
           ".html")
   starintel-pages--site))

(defun starintel-pages--url (path)
  (mapconcat
   (lambda (part)
     (if (member part '("." ".." "")) part (url-hexify-string part)))
   (split-string (replace-regexp-in-string "\\\\" "/" path) "/")
   "/"))

(defun starintel-pages--href (from to &optional fragment)
  (concat (starintel-pages--url
           (file-relative-name to (file-name-directory from)))
          (when fragment (concat "#" (url-hexify-string fragment)))))

(defun starintel-pages--node-href (node current)
  (starintel-pages--href
   current
   (starintel-pages--output-file (org-roam-node-file node))
   (when (> (or (org-roam-node-level node) 0) 0)
     (org-roam-node-id node))))

(defun starintel-pages--id-export (path description backend info)
  (when (eq backend 'html)
    (let ((node (org-roam-node-from-id path)))
      (unless node (error "Unresolved Org-roam ID: %s" path))
      (let ((current (starintel-pages--output-file (plist-get info :input-file))))
        (format "<a href=\"%s\">%s</a>"
                (starintel-pages--node-href node current)
                (or description
                    (org-html-encode-plain-text (org-roam-node-title node))))))))

(defun starintel-pages--root-href (current target)
  (starintel-pages--href current (expand-file-name target starintel-pages--site)))

(defun starintel-pages--header (current)
  (format
   (concat "<header class=\"site-header\">"
           "<a class=\"site-title\" href=\"%s\">%s</a>"
           "<nav><a href=\"%s\">Index</a>"
           "<a href=\"%s\">Search</a>"
           "<a href=\"%s\">Graph</a></nav></header>")
   (starintel-pages--root-href current "index.html")
   (org-html-encode-plain-text starintel-pages-site-title)
   (starintel-pages--root-href current "index.html")
   (starintel-pages--root-href current "search.html")
   (starintel-pages--root-href current "graph.html")))

(defun starintel-pages--backlinks (file current)
  (let* ((node (gethash (file-truename file) starintel-pages--file-nodes))
         (links (and node (org-roam-backlinks-get node)))
         (seen (make-hash-table :test #'equal))
         rows)
    (dolist (link links)
      (let* ((source (org-roam-backlink-source-node link))
             (file-node (gethash (file-truename (org-roam-node-file source))
                                 starintel-pages--file-nodes))
             (id (and file-node (org-roam-node-id file-node))))
        (when (and file-node (not (gethash id seen)))
          (puthash id t seen)
          (push file-node rows))))
    (concat
     "<aside class=\"backlinks\"><h2>Backlinks</h2>"
     (if rows
         (concat "<ul>"
                 (mapconcat
                  (lambda (source)
                    (format "<li><a href=\"%s\">%s</a></li>"
                            (starintel-pages--node-href source current)
                            (org-html-encode-plain-text
                             (org-roam-node-title source))))
                  (sort rows
                        (lambda (a b)
                          (string-lessp (org-roam-node-title a)
                                        (org-roam-node-title b))))
                  "")
                 "</ul>")
       "<p>No pages link here yet.</p>")
     "</aside>")))

(defun starintel-pages--inject (output backend info)
  (if (not (eq backend 'html))
      output
    (let* ((file (plist-get info :input-file))
           (current (starintel-pages--output-file file))
           (head (format
                  (concat "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                          "<link rel=\"stylesheet\" href=\"%s\">"
                          "<script defer src=\"%s\"></script>")
                  (starintel-pages--root-href current "assets/site.css")
                  (starintel-pages--root-href current "assets/site.js")))
           (header (starintel-pages--header current))
           (backlinks (starintel-pages--backlinks file current)))
      (setq output (replace-regexp-in-string "</head>"
                                              (concat head "</head>")
                                              output t t))
      (setq output (replace-regexp-in-string
                    "<body\\([^>]*\\)>"
                    (concat "<body\\1>" header)
                    output t))
      (replace-regexp-in-string "</body>"
                                (concat backlinks "</body>")
                                output t t))))

(defun starintel-pages--export-file (file)
  (let ((output (starintel-pages--output-file file)))
    (make-directory (file-name-directory output) t)
    (with-current-buffer (find-file-noselect file)
      (let ((enable-local-eval nil)
            (enable-local-variables nil)
            (org-confirm-babel-evaluate t)
            (org-export-use-babel nil)
            (org-export-with-broken-links 'mark)
            (org-html-doctype "html5")
            (org-html-html5-fancy t)
            (org-html-head-include-default-style nil)
            (org-html-head-include-scripts nil)
            (org-html-preamble nil)
            (org-html-postamble nil)
            (org-export-filter-final-output-functions
             '(starintel-pages--inject)))
        (org-export-to-file
         'html output nil nil nil nil
         '(:with-author nil :with-creator nil :with-date t
           :with-email nil :with-toc t :section-numbers nil))))
    output))

(defun starintel-pages--record (node)
  (let* ((file (org-roam-node-file node))
         (relative (file-relative-name file starintel-pages--stage))
         (source (expand-file-name relative
                                   (expand-file-name "roam"
                                                     (starintel-pages--root))))
         (modified (format-time-string
                    "%Y-%m-%dT%H:%M:%SZ"
                    (file-attribute-modification-time
                     (file-attributes source))
                    t))
         (href (concat "notes/"
                       (file-name-sans-extension
                        (replace-regexp-in-string "\\\\" "/" relative))
                       ".html"))
         (description (or (starintel-pages--keyword file "DESCRIPTION") ""))
         (tags (or (org-roam-node-tags node) '())))
    `((id . ,(org-roam-node-id node))
      (title . ,(org-roam-node-title node))
      (description . ,description)
      (url . ,href)
      (kind . ,(or (car (split-string relative "/" t)) "notes"))
      (tags . ,(vconcat tags))
      (modified . ,modified))))

(defun starintel-pages--collect ()
  (let (records)
    (maphash (lambda (_file node) (push (starintel-pages--record node) records))
             starintel-pages--file-nodes)
    (setq starintel-pages--records
          (sort records
                (lambda (a b)
                  (string-lessp (alist-get 'title a)
                                (alist-get 'title b)))))))

(defun starintel-pages--page (title body)
  (concat
   "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
   "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
   "<title>" (org-html-encode-plain-text title) "</title>"
   "<link rel=\"stylesheet\" href=\"assets/site.css\">"
   "<script defer src=\"assets/site.js\"></script></head><body>"
   (starintel-pages--header (expand-file-name "index.html" starintel-pages--site))
   "<main class=\"site-main\">" body "</main></body></html>"))

(defun starintel-pages--write (relative content)
  (let ((path (expand-file-name relative starintel-pages--site)))
    (make-directory (file-name-directory path) t)
    (with-temp-file path (insert content))))

(defun starintel-pages--record-row (record)
  (format "<li><a href=\"%s\">%s</a><span>%s</span></li>"
          (starintel-pages--url (alist-get 'url record))
          (org-html-encode-plain-text (alist-get 'title record))
          (org-html-encode-plain-text (alist-get 'modified record))))

(defun starintel-pages--write-indexes ()
  (let ((rows (mapconcat #'starintel-pages--record-row
                         starintel-pages--records "")))
    (starintel-pages--write
     "index.html"
     (starintel-pages--page
      starintel-pages-site-title
      (concat "<section class=\"hero\"><p class=\"eyebrow\">Org-roam research graph</p>"
              "<h1>StarIntel GPT Auto Dig</h1>"
              "<p>Evidence-linked research, contracts, lobbying networks and investigation indexes.</p>"
              "<p><strong>" (number-to-string (length starintel-pages--records))
              "</strong> published nodes</p></section>"
              "<section><h2>All nodes</h2><ol class=\"note-list\">"
              rows "</ol></section>")))
    (starintel-pages--write
     "search.html"
     (starintel-pages--page
      "Search — StarIntel GPT Auto Dig"
      (concat "<section><h1>Search</h1>"
              "<input id=\"search-input\" type=\"search\" autocomplete=\"off\" autofocus>"
              "<p id=\"search-status\"></p>"
              "<ol id=\"search-results\" class=\"search-results\"></ol></section>")))
    (starintel-pages--write
     "graph.html"
     (starintel-pages--page
      "Graph — StarIntel GPT Auto Dig"
      (concat "<section><h1>Graph</h1>"
              "<canvas id=\"graph-canvas\" width=\"1200\" height=\"760\"></canvas>"
              "<p id=\"graph-status\"></p></section>")))
    (starintel-pages--write
     "404.html"
     (starintel-pages--page
      "Not found — StarIntel GPT Auto Dig"
      "<section><h1>Page not found</h1></section>"))))

(defun starintel-pages--graph-links ()
  (let ((seen (make-hash-table :test #'equal)) links)
    (maphash
     (lambda (_file target)
       (dolist (backlink (org-roam-backlinks-get target))
         (let* ((source0 (org-roam-backlink-source-node backlink))
                (source (gethash (file-truename (org-roam-node-file source0))
                                 starintel-pages--file-nodes))
                (source-id (and source (org-roam-node-id source)))
                (target-id (org-roam-node-id target))
                (key (and source-id (concat source-id "->" target-id))))
           (when (and key
                      (not (string= source-id target-id))
                      (not (gethash key seen)))
             (puthash key t seen)
             (push `((source . ,source-id) (target . ,target-id)) links)))))
     starintel-pages--file-nodes)
    (nreverse links)))

(defun starintel-pages--write-json ()
  (let ((json-encoding-pretty-print t))
    (starintel-pages--write
     "search-index.json"
     (json-encode (vconcat starintel-pages--records)))
    (starintel-pages--write
     "graph.json"
     (json-encode
      `((nodes . ,(vconcat starintel-pages--records))
        (links . ,(vconcat (starintel-pages--graph-links))))))))

(defun starintel-pages--copy-assets ()
  (copy-directory
   (expand-file-name "pages/static" (starintel-pages--root))
   (expand-file-name "assets" starintel-pages--site)
   t t t)
  (starintel-pages--write ".nojekyll" ""))

(defun starintel-pages-build (&optional root)
  "Build the complete Org-roam site under `_site'."
  (interactive)
  (let ((starintel-pages-root
         (file-name-as-directory
          (file-truename (or root (starintel-pages--root))))))
    (starintel-pages--prepare)
    (starintel-pages--configure-roam)
    (org-link-set-parameters "id" :export #'starintel-pages--id-export)
    (starintel-pages--collect)
    (dolist (file starintel-pages--files)
      (starintel-pages--export-file file))
    (starintel-pages--copy-assets)
    (starintel-pages--write-json)
    (starintel-pages--write-indexes)
    (message "Published %d Org-roam pages to %s"
             (length starintel-pages--files)
             starintel-pages--site)
    starintel-pages--site))

(defalias 'star/pages-build #'starintel-pages-build)

(provide 'starintel-pages)
;;; pages.el ends here
