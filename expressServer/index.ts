import express, { type Request, type Response } from "express";

/*
2.0 with callback
You have been assigned a 
consumer token of c3a6610edb87d36ea086afbe669be4fa 
and a 
secret token of a3484c0d2a08cdd523d3f69bbdc47932b076da38. 
Please record these for future reference.
*/

/*
1.0a with callback
66e1f1994ce65fbd516b5547757919eb
You have been assigned a consumer secret token of c1955cb0a2b45aa98b9d9bd1b5c111e2ad700488. 
*/

const user_token = "355aed80-98c9-479c-836e-2d624b0c6c39";

const clientId = "cd010723955ab90f5e10ae507660b920";
const clientSecret = "de13fada4c4b6d38adfd7e9b996916675a89d18b";

const app = express();
const port = 8082;

app.get("/", (req, res) => {
  res.set("ngrok-skip-browser-warning", "true");
  res.send({ value: "Hello You" });
});

app.get("/api/v0", (req: Request, res: Response) => {
  res.send({ value: "api v0" });
});

const urlAccessToken = new URL(
  "https://bnwiki.wikibase.cloud/w/rest.php/oauth2/access_token"
);

const toFormURLEncode = (data: Record<string, string>): string => {
  const tmp = Object.entries(data)
    .map(
      ([key, value]) =>
        `${encodeURIComponent(key)}=${encodeURIComponent(value)}`
    )
    .join("&");
  console.log("Tmp:", tmp);
  return tmp;
};

app.get("/oAuth/:userId", (req, res) => {
  console.log(req);
  // check if userId exists
  if (req.params.userId === user_token) {
    //const code = req.query.code;
    const oauthVerifier = req.query.oauth_verifier;
    const oauthToken = req.query.oauth_token;

    if (oauthVerifier && oauthToken) {
      const headers = new Headers();
      headers.set("Content-Type", "application/x-www-form-urlencoded");

      /*
      const body = toFormURLEncode({
        grant_type: "authorization_code",
        code: code as string,
        client_id: clientId,
        client_secret: clientSecret,
      });
      */

      const urlAccessTokenCopy = new URL(urlAccessToken);
      //urlAccessTokenCopy.searchParams.set("grant_type", "authorization_code");
      //urlAccessTokenCopy.searchParams.set("code", "authorization_code");
      //urlAccessTokenCopy.searchParams.set("client_id", clientId);
      //urlAccessTokenCopy.searchParams.set("client_secret", clientSecret);

      /*
      fetch(urlAccessTokenCopy, {
        method: "POST",
        headers: headers,
        body: body,
      }).then(
        (fulfilled) => {
          console.log(fulfilled);
          res.send({ value: fulfilled });
        },
        (errorReason) => {
          console.log(errorReason);
          res.send({ value: errorReason });
        }
      );
      */
      res.send({ value: "wait" });
    } else {
      res.send({ value: "No Code" });
    }
  } else {
    res.send({ value: "Denied" });
  }
});

app.listen(port, () => {
  console.log("Server is running");
});
