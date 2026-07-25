((org-mode
  . ((eval . (let* ((root (locate-dominating-file default-directory "AGENTS.md"))
                    (roam (and root (expand-file-name "roam" root)))
                    (cache (and root (expand-file-name ".cache" root))))
               (when root
                 (setq-local org-roam-directory (file-truename roam)
                             org-roam-db-location (expand-file-name "org-roam.db" cache)
                             org-id-locations-file (expand-file-name "org-id-locations" cache))))))))
