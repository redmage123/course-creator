# Fix shared imports in the main app template
s/from shared\.database/from ...shared.database/g
s/from shared\.middleware/from ...shared.middleware/g
s/from shared\.config/from ...shared.config/g
s/config_manager\.get_config(/config_manager.get(/g
