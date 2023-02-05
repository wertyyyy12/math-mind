import React from "react";

function ImageUpload({
  setSelectedImg,
  label,
}: {
  setSelectedImg: (img: File) => void;
  label: string;
}): React.ReactElement {
  return (
    <>
      <div>{label}</div>
      <input
        type="file" // could screw things up, use "image" if it does
        name="studentWork"
        onChange={(e) => {
          if (e && e.target && e.target.files && e.target.files[0]) {
            setSelectedImg(e.target.files[0]);
          } else {
            console.log("didn't set image");
          }
        }}
      ></input>
    </>
  );
}

export default ImageUpload;
