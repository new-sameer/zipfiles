$(document).ready(function () {
    $("#find_btn").click(function () { //user clicks button
        if ("geolocation" in navigator){ //check geolocation available
            //try to get user current location using getCurrentPosition() method
            navigator.geolocation.getCurrentPosition(function(position){
                    $("#location-results").html("Found your location <br />Lat : <label id='latitude'> "+position.coords.latitude+"</label> </br>Lang :<label id='longitude'>"+ position.coords.longitude+"</label>");
                });
        }else{
            console.log("Browser doesn't support geolocation!");
        }
    });
    $(document).on('click','#startbutton',function () {

        $('#upload-button').prop('disabled', false);
    })
    $(document).on('click','#upload-button',function () {
        let new_image=$('#photo').attr('src');
        let csrf=$('input[name="csrfmiddlewaretoken"]').val();
        let url='/attendance/login/';
        let latitude=$('#latitude').text();
        let longitude=$('#longitude').text();
        if (latitude===''){
            alert('You have to provide your current location first. Please click on the find me button.')
        }else{
            $.ajax({
            url:url,
            method:'post',
            dataType:'json',
            data:{
                'image_data':new_image,
                'csrfmiddlewaretoken': csrf,
                'latitude':latitude,
                'longitude':longitude,
            },
            success:function (data) {
                window.location.href='/'
            }
        })
        }


    })
    function readURL(input) {
      if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function(e) {
          $('#photo').attr('src', e.target.result);
        }

        reader.readAsDataURL(input.files[0]); // convert to base64 string
      }
    }

    $("#mobile-input").change(function() {
      readURL(this);
    });
    $('#id_date_range').change(function (){
        let date_range=$(this).val()
        let start_date=date_range.split(' - ')[0]
        let end_date=date_range.split(' - ')[1]
        let date1 = new Date(start_date);
        let date2 = new Date(end_date);
        let diffTime = Math.abs(date2 - date1);
        let diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))+1;
        $('#id_no_of_days').val(diffDays);
    })

    $('#download_bills').on('click',function (e) {
        let oa_number=$("input[name=oa_number]").val();
    });
    $('body').on('click','img.upload-image',function (e) {
        let image_url=$(this).attr('src');
        $('#preview-image').attr('src',image_url);
    })

})