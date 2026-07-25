;;; second-brain.el --- Org-roam configuration for GPT auto-dig -*- lexical-binding: t; -*-

(require 'org)
(require 'org-id)
(require 'org-roam)

(defun starintel-second-brain-configure (&optional root interactive)
  "Configure Org-roam beneath ROOT.
When INTERACTIVE is non-nil, enable database updates on save."
  (let* ((repo (file-name-as-directory
                (file-truename
                 (or root
                     (locate-dominating-file default-directory "AGENTS.md")
                     (error "Cannot locate repository root")))))
         (roam (expand-file-name "roam" repo))
         (cache (expand-file-name ".cache" repo)))
    (make-directory cache t)
    (setq org-roam-directory (file-truename roam)
          org-roam-db-location (expand-file-name "org-roam.db" cache)
          org-id-locations-file (expand-file-name "org-id-locations" cache)
          org-roam-db-update-on-save interactive)
    (when interactive
      (org-roam-db-autosync-mode 1))
    (require 'starintel-pages)
    repo))

(defun star/roam ()
  "Open the canonical publication index."
  (interactive)
  (find-file
   (expand-file-name
    "indexes/second-brain/SECOND-BRAIN-000-org-roam-pages.org"
    org-roam-directory)))

(defun star/roam-sync ()
  "Synchronize the Org-roam database."
  (interactive)
  (org-roam-db-sync))

(provide 'starintel-second-brain)
;;; second-brain.el ends here
