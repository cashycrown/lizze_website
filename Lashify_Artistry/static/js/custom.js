
  (function ($) {
  
  "use strict";

    // COUNTER NUMBERS
    jQuery('.counter-thumb').appear(function() {
      jQuery('.counter-number').countTo();
    });

      // BACKSTRETCH SLIDESHOW
    // var heroSection = $('#hero-slideshow');
    // var imageData = heroSection.data('images');

    // if (imageData && imageData.length > 0) {
    //   heroSection.backstretch(imageData, {
    //     duration: 2000,
    //     fade: 750
    //   });
    // }

    // CUSTOM LINK
    $('.smoothscroll').click(function(){
      var el = $(this).attr('href');
      var elWrapped = $(el);
  
      scrollToDiv(elWrapped);
      return false;
  
      function scrollToDiv(element){
        var offset = element.offset();
        var offsetTop = offset.top;
        var totalScroll = offsetTop-navheight;
  
        $('body,html').animate({
        scrollTop: totalScroll
        }, 300);
      }
    });
    
  })(window.jQuery);


  document.addEventListener("DOMContentLoaded", function () {
    const slides = document.querySelectorAll(".hero-slideshow .slide");
    let currentIndex = 0;
    const delay = 3000; // 3 seconds per slide

    function showSlide(index) {
      slides.forEach((slide, i) => {
        slide.classList.remove("active");
        if (i === index) slide.classList.add("active");
      });
    }

    function nextSlide() {
      currentIndex = (currentIndex + 1) % slides.length;
      showSlide(currentIndex);
    }

    setInterval(nextSlide, delay);
  });

