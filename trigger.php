
<?php
      $urlPDF = 'http://bpm.nearshoremx.com/sysNDS/es/neoclassic/cases/cases_ShowDocument?a=6603468915a9d8234905bf0040436412&v=1';

      $postData = array(
         'url' =>  $urlPDF,
         'word' => 'objeto'
      );

      $context = stream_context_create(array(
        'http' => array(
          // http://www.php.net/manual/en/context.http.php
        'method' => 'POST',
        'header' => "Content-Type: application/json\r\n",
        'content' => json_encode($postData)
      	)
      ));

      ini_set('default_socket_timeout', 900);

      //Send the request
      $response = file_get_contents('http://localhost:5000/acta', FALSE, $context);

      // Check for errors
      if($response === FALSE){
        die('Error');
      }

      class Text
      {
        public $text;
        public $categories;
        public $concepts;
      }

      // Decode the response
      $responseData = json_decode($response, TRUE);
      //echo "hola";
      //echo $responseData[0]['text'];

      $resultJson = new Text();

      $resultJson->text = $responseData[0]['text'];

      echo $resultJson->text;

      //echo $responseData['code'];
      //echo "\n";

       /*@@cat0 = $responseData['cat0'];
       @@cat1 = $responseData['cat1'];
       @@cat2 = $responseData['cat2'];
       @@cw1 = $responseData['cw1'];
       @@cw2 = $responseData['cw2'];
       @@cw3 = $responseData['cw3'];*/

      /* $textStatus = $responseData['code'];
       if($textStatus == 'ALERT'){
      	@@alert = 0;
       } else {
      	  @@alert = 0;
       }
    }*/
?>
