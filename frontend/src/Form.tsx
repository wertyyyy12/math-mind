import React, { useState } from "react";
import FileUpload from "./ImageUpload";
const FLASK_PORT = 7000;

function Form(): React.ReactElement {
  const [selectedImg, setSelectedImg] = useState<File>();
  return (
    <div>
      <FileUpload setSelectedImg={setSelectedImg} label={"image"} />
      <button
        onClick={(e) => {
          if (selectedImg) {
            console.log({ selectedImg });
            const url = "http://127.0.0.1:" + FLASK_PORT + "/";
            const data = new FormData();
            data.append("question", "2x+1==6");
            data.append("imgFile", selectedImg);
            // data.append("audioBlobURL", selectedAudio!);
            fetch(url, {
              method: "POST",
              body: data,
              mode: "cors",
            }).then((res) => {
              console.log({ res });
            });

            // const fData = new FormData();
            // fData.append("image", selectedImg);
            // fetch("https://api.imgur.com/3/upload", {
            //   method: "POST",
            //   headers: {
            //     Authorization: "Client ID c454c20af584075",
            //     Accept: "HTTP/1.1",
            //   },
            //   body: fData,
            // })
            //   .then((data) => data.json())
            //   .then((res) => {
            //     console.log({ res });
            //     console.log(res.link);
            //   });

            // axios({
            //   method: "get",
            //   url: "http://127.0.0.1:" + FLASK_PORT + "/",
            //   data: {
            //     question: "2x+3==1",
            //     imgBlobURL: selectedImg,
            //     studentWork: "test",
            //   },
            // });
          } else {
            console.log("didn't select img");
          }
        }}
      >
        Submit
      </button>
    </div>
  );
}

export default Form;
