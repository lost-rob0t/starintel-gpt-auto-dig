;;; bootstrap.el --- Batch bootstrap for StarIntel GPT Auto Dig -*- lexical-binding: t; -*-

(let* ((pages-directory
        (file-name-directory (or load-file-name buffer-file-name)))
       (root (file-name-directory (directory-file-name pages-directory)))
       (cache (expand-file-name ".cache/emacs" root))
       (lisp-directory (expand-file-name "lisp/starintel" root)))
  (setq package-user-dir (expand-file-name "elpa" cache))
  (require 'package)
  (setq package-archives
        '(("gnu" . "https://elpa.gnu.org/packages/")
          ("nongnu" . "https://elpa.nongnu.org/nongnu/")
          ("melpa" . "https://melpa.org/packages/")))
  (package-initialize)
  (unless (and (package-installed-p 'org-roam '(2 3 1))
               (package-installed-p 'htmlize))
    (package-refresh-contents)
    (unless (package-installed-p 'org-roam '(2 3 1))
      (package-install 'org-roam))
    (unless (package-installed-p 'htmlize)
      (package-install 'htmlize)))
  (add-to-list 'load-path lisp-directory)
  (require 'starintel-second-brain)
  (starintel-second-brain-configure root nil)
  (starintel-pages-build root))

;;; bootstrap.el ends here
