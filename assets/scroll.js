window.dash_clientside = {
    clientside: {
        scrollToTop: function(n_clicks) {
            if (n_clicks > 0) {
                window.scrollTo({ top: 0, behavior: "smooth" });  // Smooth scroll
                return 0;  // Reset click count
            }
            return window.dash_clientside.no_update;
        }
    }
};